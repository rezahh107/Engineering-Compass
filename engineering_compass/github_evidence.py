from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .model import ContractError, canonical_target, finalize_evidence_bundle, require, validate_request

API = "https://api.github.com"
PR_CHANGED_FILES_LIMIT = 3000
COMPARE_CHANGED_FILES_LIMIT = 300


class GitHubEvidenceCollector:
    """Read-only GitHub REST collector for exact target identity and bounded review evidence."""

    def __init__(self, token: str | None = None, timeout: int = 20):
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout

    def _request(self, path: str, *, accept: str = "application/vnd.github+json") -> tuple[Any, dict[str, str]]:
        url = path if path.startswith("https://") else f"{API}{path}"
        headers = {
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Engineering-Compass/0.1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw), {k.lower(): v for k, v in response.headers.items()}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ContractError(f"GitHub HTTP {exc.code} for {url}: {body[:400]}") from exc
        except urllib.error.URLError as exc:
            raise ContractError(f"GitHub request failed for {url}: {exc}") from exc


    def _paginate(self, path: str, *, max_pages: int = 100) -> tuple[list[Any], bool]:
        page = 1
        out: list[Any] = []
        while True:
            sep = "&" if "?" in path else "?"
            payload, _ = self._request(f"{path}{sep}per_page=100&page={page}")
            require(isinstance(payload, list), f"expected paginated list from {path}")
            out.extend(payload)
            if len(payload) < 100:
                return out, True
            if page >= max_pages:
                return out, False
            page += 1



    @staticmethod
    def _evidence_record(eid: str, kind: str, source: str, payload: Any, *, limitations: list[str] | None = None) -> dict[str, Any]:
        return {"evidence_id": eid, "kind": kind, "source": source, "payload": payload, "limitations": limitations or []}

    @staticmethod
    def _missing_patch_files(files: list[Any]) -> list[str]:
        return sorted(
            str(item.get("filename") or "<unknown>")
            for item in files
            if isinstance(item, dict) and not isinstance(item.get("patch"), str)
        )



    def collect(self, request: dict[str, Any]) -> dict[str, Any]:
        validate_request(request)
        canonical_request = dict(request)
        canonical_request["target"] = canonical_target(request["target"])
        kind = canonical_request["target"]["kind"]
        if kind == "PR_SCOPE":
            return self._collect_pr(canonical_request)
        if kind == "REF_DELTA_SCOPE":
            return self._collect_ref_delta(canonical_request)
        if kind == "REPOSITORY_SCOPE":
            return self._collect_repository(canonical_request)
        raise ContractError(f"unsupported target kind: {kind}")


    def _repo(self, repository: str) -> dict[str, Any]:
        repo, _ = self._request(f"/repos/{repository}")
        require(isinstance(repo, dict), "repository response must be object")
        return repo


    def _collect_pr(self, request: dict[str, Any]) -> dict[str, Any]:
        target = canonical_target(request["target"])
        repo_name, pr_number = target["repository"], target["pr_number"]
        repo = self._repo(repo_name)
        pr, _ = self._request(f"/repos/{repo_name}/pulls/{pr_number}")
        require(isinstance(pr, dict), "pull request response must be object")
        files, _ = self._paginate(f"/repos/{repo_name}/pulls/{pr_number}/files", max_pages=30)
        reviews, reviews_complete = self._paginate(f"/repos/{repo_name}/pulls/{pr_number}/reviews")
        comments, comments_complete = self._paginate(f"/repos/{repo_name}/issues/{pr_number}/comments")
        review_comments, review_comments_complete = self._paginate(f"/repos/{repo_name}/pulls/{pr_number}/comments")

        expected_changed_files = pr.get("changed_files")
        require(isinstance(expected_changed_files, int) and expected_changed_files >= 0, "pull request changed_files count missing")
        files_inventory_complete = len(files) == expected_changed_files and expected_changed_files <= PR_CHANGED_FILES_LIMIT
        missing_patches = self._missing_patch_files(files)
        diff_content_complete = files_inventory_complete and not missing_patches
        base_sha, head_sha = pr["base"]["sha"], pr["head"]["sha"]
        compare, _ = self._request(f"/repos/{repo_name}/compare/{base_sha}...{head_sha}")
        merge_base_sha = compare.get("merge_base_commit", {}).get("sha") if isinstance(compare, dict) else None

        checks: list[Any] = []
        checks_complete = True
        check_limitations: list[str] = []
        try:
            payload, _ = self._request(f"/repos/{repo_name}/commits/{head_sha}/check-runs?per_page=100", accept="application/vnd.github+json")
            if isinstance(payload, dict):
                checks = payload.get("check_runs", [])
                total = int(payload.get("total_count", len(checks)))
                checks_complete = total <= len(checks)
                if not checks_complete:
                    check_limitations.append("check-runs response exceeded first page; exact completeness not proven")
        except ContractError as exc:
            checks_complete = False
            check_limitations.append(str(exc))

        gaps: list[str] = []
        if not files_inventory_complete:
            gaps.append("pr_changed_files_inventory_incomplete")
        if expected_changed_files > PR_CHANGED_FILES_LIMIT:
            gaps.append("pr_changed_files_cap_exceeded")
        if not diff_content_complete:
            gaps.append("pr_diff_content_incomplete")
        if not all([reviews_complete, comments_complete, review_comments_complete, checks_complete]):
            gaps.append("one_or_more_PR_evidence_surfaces_incomplete")
        completeness = {
            "full_coverage": not gaps,
            "material_gaps": sorted(set(gaps)),
            "surfaces": {
                "changed_file_inventory": files_inventory_complete,
                "diff_content": diff_content_complete,
                "reviews": reviews_complete,
                "conversation_comments": comments_complete,
                "inline_review_comments": review_comments_complete,
                "checks": checks_complete,
            },
        }
        diff_limitations: list[str] = []
        if not files_inventory_complete:
            diff_limitations.append(f"changed-file inventory incomplete: expected {expected_changed_files}, enumerated {len(files)}")
        if missing_patches:
            diff_limitations.append(f"patch content unavailable for {len(missing_patches)} file(s): {', '.join(missing_patches[:10])}")

        evidence_records = [
            self._evidence_record("EVD-REPO", "REPOSITORY", f"GET /repos/{repo_name}", {"id": repo.get("id"), "full_name": repo.get("full_name"), "default_branch": repo.get("default_branch")}),
            self._evidence_record("EVD-PR", "PULL_REQUEST", f"GET /repos/{repo_name}/pulls/{pr_number}", {"number": pr.get("number"), "state": pr.get("state"), "draft": pr.get("draft"), "changed_files": expected_changed_files, "base_ref": pr["base"]["ref"], "base_sha": base_sha, "head_ref": pr["head"]["ref"], "head_sha": head_sha}),
            self._evidence_record("EVD-DIFF", "CHANGED_FILES", f"GET /repos/{repo_name}/pulls/{pr_number}/files", [{"filename": item.get("filename"), "status": item.get("status"), "additions": item.get("additions"), "deletions": item.get("deletions"), "changes": item.get("changes"), "patch": item.get("patch")} for item in files], limitations=diff_limitations),
            self._evidence_record("EVD-CHECKS", "CHECK_RUNS", f"GET /repos/{repo_name}/commits/{head_sha}/check-runs", [{"name": item.get("name"), "status": item.get("status"), "conclusion": item.get("conclusion"), "app": {"id": (item.get("app") or {}).get("id"), "slug": (item.get("app") or {}).get("slug")}, "details_url": item.get("details_url"), "head_sha": item.get("head_sha")} for item in checks], limitations=check_limitations),
            self._evidence_record("EVD-REVIEWS", "REVIEWS", f"GET /repos/{repo_name}/pulls/{pr_number}/reviews", [{"id": item.get("id"), "state": item.get("state"), "user": (item.get("user") or {}).get("login"), "submitted_at": item.get("submitted_at"), "commit_id": item.get("commit_id"), "body": item.get("body")} for item in reviews], limitations=[] if reviews_complete else ["pagination incomplete"]),
            self._evidence_record("EVD-COMMENTS", "COMMENTS", f"PR conversation + inline review comments for #{pr_number}", {"conversation": comments, "inline": review_comments}, limitations=[] if comments_complete and review_comments_complete else ["pagination incomplete"]),
        ]
        return finalize_evidence_bundle({
            "schema_version": 2,
            "collected_at_epoch": int(time.time()),
            "target": target,
            "review_intent": request["review_intent"],
            "identity": {"repository_id": str(repo["id"]), "base_ref": pr["base"]["ref"], "base_sha": base_sha, "head_ref": pr["head"]["ref"], "head_sha": head_sha, "merge_base_sha": merge_base_sha, "pr_state": pr.get("state")},
            "freshness": "CURRENT",
            "completeness": completeness,
            "evidence_records": evidence_records,
        })



    def _collect_ref_delta(self, request: dict[str, Any]) -> dict[str, Any]:
        target = canonical_target(request["target"])
        repo_name = target["repository"]
        repo = self._repo(repo_name)
        base = urllib.parse.quote(target["base_ref"], safe="")
        head = urllib.parse.quote(target["target_ref"], safe="")
        compare, _ = self._request(f"/repos/{repo_name}/compare/{base}...{head}")
        require(isinstance(compare, dict), "compare response must be object")
        files = compare.get("files", []) or []
        require(isinstance(files, list), "compare files must be a list")
        base_sha = compare.get("base_commit", {}).get("sha")
        head_sha = compare.get("head_commit", {}).get("sha")
        merge_base_sha = compare.get("merge_base_commit", {}).get("sha")
        cap_reached = len(files) >= COMPARE_CHANGED_FILES_LIMIT
        missing_patches = self._missing_patch_files(files)
        inventory_complete = not cap_reached
        diff_content_complete = inventory_complete and not missing_patches
        gaps: list[str] = []
        if cap_reached:
            gaps.append("compare_changed_files_cap_reached")
        if missing_patches:
            gaps.append("compare_diff_content_incomplete")
        limitations: list[str] = []
        if cap_reached:
            limitations.append("Compare API changed-file list reached the 300-file ceiling; exact inventory is not proven")
        if missing_patches:
            limitations.append(f"patch content unavailable for {len(missing_patches)} file(s): {', '.join(missing_patches[:10])}")
        evidence = self._evidence_record("EVD-COMPARE", "REF_COMPARISON", f"compare {target['base_ref']}...{target['target_ref']}", {
            "status": compare.get("status"), "ahead_by": compare.get("ahead_by"), "behind_by": compare.get("behind_by"),
            "files": [{"filename": item.get("filename"), "status": item.get("status"), "changes": item.get("changes"), "patch": item.get("patch")} for item in files],
        }, limitations=limitations)
        return finalize_evidence_bundle({
            "schema_version": 2,
            "collected_at_epoch": int(time.time()),
            "target": target,
            "review_intent": request["review_intent"],
            "identity": {"repository_id": str(repo["id"]), "base_ref": target["base_ref"], "base_sha": base_sha, "head_ref": target["target_ref"], "head_sha": head_sha, "merge_base_sha": merge_base_sha},
            "freshness": "CURRENT",
            "completeness": {"full_coverage": not gaps, "material_gaps": gaps, "surfaces": {"changed_file_inventory": inventory_complete, "diff_content": diff_content_complete}},
            "evidence_records": [self._evidence_record("EVD-REPO", "REPOSITORY", f"GET /repos/{repo_name}", {"id": repo.get("id"), "full_name": repo.get("full_name")}), evidence],
        })



    def _collect_repository(self, request: dict[str, Any]) -> dict[str, Any]:
        target = canonical_target(request["target"])
        repo_name, requested_ref = target["repository"], target["ref"]
        ref = urllib.parse.quote(requested_ref, safe="")
        repo = self._repo(repo_name)
        commit, _ = self._request(f"/repos/{repo_name}/commits/{ref}")
        require(isinstance(commit, dict), "commit response must be object")
        head_sha = commit.get("sha")
        tree_sha = commit.get("commit", {}).get("tree", {}).get("sha")
        require(isinstance(tree_sha, str), "commit tree SHA missing")
        tree, _ = self._request(f"/repos/{repo_name}/git/trees/{tree_sha}?recursive=1")
        require(isinstance(tree, dict), "tree response must be object")
        truncated = bool(tree.get("truncated"))
        entries = tree.get("tree", []) or []
        return finalize_evidence_bundle({
            "schema_version": 2,
            "collected_at_epoch": int(time.time()),
            "target": target,
            "review_intent": request["review_intent"],
            "identity": {"repository_id": str(repo["id"]), "head_ref": requested_ref, "head_sha": head_sha, "base_sha": None, "merge_base_sha": None},
            "freshness": "CURRENT",
            "completeness": {"full_coverage": not truncated, "material_gaps": ["recursive_tree_truncated"] if truncated else [], "surfaces": {"repository_tree": not truncated}},
            "evidence_records": [
                self._evidence_record("EVD-REPO", "REPOSITORY", f"GET /repos/{repo_name}", {"id": repo.get("id"), "full_name": repo.get("full_name"), "default_branch": repo.get("default_branch")}),
                self._evidence_record("EVD-SNAPSHOT", "REPOSITORY_SNAPSHOT", f"commit/tree at {requested_ref}", {"commit_sha": head_sha, "tree_sha": tree_sha, "paths": [{"path": item.get("path"), "type": item.get("type"), "sha": item.get("sha"), "size": item.get("size")} for item in entries]}, limitations=["recursive tree truncated"] if truncated else []),
            ],
        })
