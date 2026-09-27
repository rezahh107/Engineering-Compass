from __future__ import annotations

import base64
import binascii
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .model import ContractError, canonical_target, finalize_evidence_bundle, require, validate_request

API = "https://api.github.com"
GRAPHQL_API = "https://api.github.com/graphql"
PR_CHANGED_FILES_LIMIT = 3000
COMPARE_CHANGED_FILES_LIMIT = 300
REPOSITORY_SOURCE_MAX_FILES = 250
REPOSITORY_SOURCE_MAX_TOTAL_BYTES = 4 * 1024 * 1024
REPOSITORY_SOURCE_MAX_BLOB_BYTES = 512 * 1024
REVIEW_THREAD_MAX_PAGES = 100
REVIEW_THREAD_COMMENT_MAX_PAGES = 100

_REVIEW_THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $after) {
        nodes {
          id isResolved isOutdated path line originalLine startLine originalStartLine
          diffSide startDiffSide subjectType
          comments(first: 100) {
            nodes { id body author { login } authorAssociation createdAt lastEditedAt url }
            pageInfo { hasNextPage endCursor }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

_REVIEW_THREAD_COMMENTS_QUERY = """
query($threadId: ID!, $after: String) {
  node(id: $threadId) {
    ... on PullRequestReviewThread {
      comments(first: 100, after: $after) {
        nodes { id body author { login } authorAssociation createdAt lastEditedAt url }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""


class GitHubEvidenceCollector:
    """Read-only GitHub REST collector for exact target identity and bounded review evidence."""

    def __init__(
        self,
        token: str | None = None,
        timeout: int = 20,
        *,
        repository_source_max_files: int = REPOSITORY_SOURCE_MAX_FILES,
        repository_source_max_total_bytes: int = REPOSITORY_SOURCE_MAX_TOTAL_BYTES,
        repository_source_max_blob_bytes: int = REPOSITORY_SOURCE_MAX_BLOB_BYTES,
    ):
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout
        for value, name in [
            (repository_source_max_files, "repository_source_max_files"),
            (repository_source_max_total_bytes, "repository_source_max_total_bytes"),
            (repository_source_max_blob_bytes, "repository_source_max_blob_bytes"),
        ]:
            require(isinstance(value, int) and value >= 0, f"{name} must be a non-negative integer")
        self.repository_source_max_files = repository_source_max_files
        self.repository_source_max_total_bytes = repository_source_max_total_bytes
        self.repository_source_max_blob_bytes = repository_source_max_blob_bytes

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


    def _graphql_request(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Engineering-Compass/0.1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(
            GRAPHQL_API,
            headers=headers,
            data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ContractError(f"GitHub GraphQL HTTP {exc.code}: {body[:400]}") from exc
        except urllib.error.URLError as exc:
            raise ContractError(f"GitHub GraphQL request failed: {exc}") from exc
        require(isinstance(payload, dict), "GitHub GraphQL response must be an object")
        require(not payload.get("errors"), f"GitHub GraphQL errors: {json.dumps(payload.get('errors'), ensure_ascii=False)[:400]}")
        data = payload.get("data")
        require(isinstance(data, dict), "GitHub GraphQL response omitted data")
        return data


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


    @staticmethod
    def _normalize_status(item: Any) -> dict[str, Any]:
        status = item if isinstance(item, dict) else {}
        creator = status.get("creator") if isinstance(status.get("creator"), dict) else {}
        return {
            "context": status.get("context"), "state": status.get("state"),
            "description": status.get("description"), "target_url": status.get("target_url"),
            "creator": {"login": creator.get("login"), "id": creator.get("id")},
            "created_at": status.get("created_at"), "updated_at": status.get("updated_at"),
        }

    @staticmethod
    def _normalize_review_comment(item: Any) -> dict[str, Any]:
        comment = item if isinstance(item, dict) else {}
        author = comment.get("author") if isinstance(comment.get("author"), dict) else {}
        return {
            "id": comment.get("id"), "body": comment.get("body"),
            "author": {"login": author.get("login")},
            "authorAssociation": comment.get("authorAssociation"),
            "createdAt": comment.get("createdAt"), "lastEditedAt": comment.get("lastEditedAt"),
            "url": comment.get("url"),
        }

    def _collect_commit_statuses(self, repo_name: str, head_sha: str) -> tuple[list[Any], bool, list[str]]:
        try:
            statuses, complete = self._paginate(f"/repos/{repo_name}/commits/{head_sha}/statuses")
        except ContractError as exc:
            return [], False, [str(exc)]
        limitations = [] if complete else ["commit-status pagination limit reached; exact status-list completeness not proven"]
        return statuses, complete, limitations

    def _paginate_review_thread_comments(
        self, thread_id: str, connection: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], bool, list[str]]:
        nodes = connection.get("nodes", [])
        require(isinstance(nodes, list), "review-thread comments nodes must be a list")
        comments = [self._normalize_review_comment(item) for item in nodes]
        page_info = connection.get("pageInfo")
        require(isinstance(page_info, dict), "review-thread comments pageInfo missing")
        pages = 1
        limitations: list[str] = []
        while page_info.get("hasNextPage") is True:
            if pages >= REVIEW_THREAD_COMMENT_MAX_PAGES:
                limitations.append(f"review-thread comment pagination limit reached for {thread_id}")
                return comments, False, limitations
            cursor = page_info.get("endCursor")
            require(isinstance(cursor, str) and cursor, "review-thread comments next page omitted endCursor")
            try:
                data = self._graphql_request(_REVIEW_THREAD_COMMENTS_QUERY, {"threadId": thread_id, "after": cursor})
                node = data.get("node")
                require(isinstance(node, dict), f"review-thread {thread_id} comment pagination omitted node")
                connection = node.get("comments")
                require(isinstance(connection, dict), f"review-thread {thread_id} comment pagination omitted comments")
                next_nodes = connection.get("nodes", [])
                require(isinstance(next_nodes, list), "review-thread comments nodes must be a list")
                comments.extend(self._normalize_review_comment(item) for item in next_nodes)
                page_info = connection.get("pageInfo")
                require(isinstance(page_info, dict), "review-thread comments pageInfo missing")
            except ContractError as exc:
                limitations.append(str(exc))
                return comments, False, limitations
            pages += 1
        return comments, True, limitations

    def _collect_review_threads(
        self, repo_name: str, pr_number: int
    ) -> tuple[list[dict[str, Any]], bool, list[str]]:
        owner, name = repo_name.split("/", 1)
        threads: list[dict[str, Any]] = []
        limitations: list[str] = []
        cursor: str | None = None
        pages = 0
        try:
            while True:
                if pages >= REVIEW_THREAD_MAX_PAGES:
                    limitations.append("review-thread pagination limit reached; exact thread topology completeness not proven")
                    return threads, False, limitations
                data = self._graphql_request(
                    _REVIEW_THREADS_QUERY,
                    {"owner": owner, "name": name, "number": pr_number, "after": cursor},
                )
                repository = data.get("repository")
                require(isinstance(repository, dict), "review-thread query omitted repository")
                pull_request = repository.get("pullRequest")
                require(isinstance(pull_request, dict), "review-thread query omitted pull request")
                connection = pull_request.get("reviewThreads")
                require(isinstance(connection, dict), "review-thread query omitted reviewThreads")
                nodes = connection.get("nodes", [])
                require(isinstance(nodes, list), "reviewThreads.nodes must be a list")
                for raw in nodes:
                    thread = raw if isinstance(raw, dict) else {}
                    thread_id = thread.get("id")
                    require(isinstance(thread_id, str) and thread_id, "review thread omitted id")
                    comments_connection = thread.get("comments")
                    require(isinstance(comments_connection, dict), f"review thread {thread_id} omitted comments")
                    comments, comments_complete, comment_limits = self._paginate_review_thread_comments(
                        thread_id, comments_connection
                    )
                    limitations.extend(comment_limits)
                    threads.append({
                        "id": thread_id, "isResolved": thread.get("isResolved"),
                        "isOutdated": thread.get("isOutdated"), "path": thread.get("path"),
                        "line": thread.get("line"), "originalLine": thread.get("originalLine"),
                        "startLine": thread.get("startLine"), "originalStartLine": thread.get("originalStartLine"),
                        "diffSide": thread.get("diffSide"), "startDiffSide": thread.get("startDiffSide"),
                        "subjectType": thread.get("subjectType"), "comments": comments,
                        "comments_complete": comments_complete,
                    })
                    if not comments_complete:
                        return threads, False, limitations
                page_info = connection.get("pageInfo")
                require(isinstance(page_info, dict), "reviewThreads.pageInfo missing")
                pages += 1
                if page_info.get("hasNextPage") is not True:
                    return threads, True, limitations
                cursor = page_info.get("endCursor")
                require(isinstance(cursor, str) and cursor, "reviewThreads next page omitted endCursor")
        except ContractError as exc:
            limitations.append(str(exc))
            return threads, False, limitations



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
            else:
                checks_complete = False
                check_limitations.append("check-runs response was not an object")
        except ContractError as exc:
            checks_complete = False
            check_limitations.append(str(exc))

        statuses, statuses_complete, status_limitations = self._collect_commit_statuses(repo_name, head_sha)
        review_threads, review_threads_complete, thread_limitations = self._collect_review_threads(
            repo_name, pr_number
        )

        initial_selector = {
            "base_ref": pr["base"]["ref"],
            "base_sha": base_sha,
            "head_ref": pr["head"]["ref"],
            "head_sha": head_sha,
            "state": pr.get("state"),
        }
        final_pr, _ = self._request(f"/repos/{repo_name}/pulls/{pr_number}")
        require(isinstance(final_pr, dict), "pull request stabilization response must be object")
        final_selector = {
            "base_ref": final_pr["base"]["ref"],
            "base_sha": final_pr["base"]["sha"],
            "head_ref": final_pr["head"]["ref"],
            "head_sha": final_pr["head"]["sha"],
            "state": final_pr.get("state"),
        }
        target_stable = initial_selector == final_selector

        gaps: list[str] = []
        if not files_inventory_complete:
            gaps.append("pr_changed_files_inventory_incomplete")
        if expected_changed_files > PR_CHANGED_FILES_LIMIT:
            gaps.append("pr_changed_files_cap_exceeded")
        if not diff_content_complete:
            gaps.append("pr_diff_content_incomplete")
        if not statuses_complete:
            gaps.append("pr_commit_statuses_incomplete")
        if not review_threads_complete:
            gaps.append("pr_review_threads_incomplete")
        if not target_stable:
            gaps.append("target_selector_moved_during_collection")
        if not all([
            reviews_complete,
            comments_complete,
            review_comments_complete,
            checks_complete,
            statuses_complete,
            review_threads_complete,
        ]):
            gaps.append("one_or_more_PR_evidence_surfaces_incomplete")
        completeness = {
            "full_coverage": not gaps,
            "material_gaps": sorted(set(gaps)),
            "surfaces": {
                "target_stabilization": target_stable,
                "changed_file_inventory": files_inventory_complete,
                "diff_content": diff_content_complete,
                "reviews": reviews_complete,
                "conversation_comments": comments_complete,
                "inline_review_comments": review_comments_complete,
                "checks": checks_complete,
                "commit_statuses": statuses_complete,
                "review_threads": review_threads_complete,
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
            self._evidence_record("EVD-STATUSES", "COMMIT_STATUSES", f"GET /repos/{repo_name}/commits/{head_sha}/statuses", {
                "head_sha": head_sha,
                "status_count": len(statuses),
                "statuses": [self._normalize_status(item) for item in statuses],
            }, limitations=status_limitations),
            self._evidence_record("EVD-REVIEWS", "REVIEWS", f"GET /repos/{repo_name}/pulls/{pr_number}/reviews", [{"id": item.get("id"), "state": item.get("state"), "user": (item.get("user") or {}).get("login"), "submitted_at": item.get("submitted_at"), "commit_id": item.get("commit_id"), "body": item.get("body")} for item in reviews], limitations=[] if reviews_complete else ["pagination incomplete"]),
            self._evidence_record("EVD-COMMENTS", "COMMENTS", f"PR conversation + inline review comments for #{pr_number}", {"conversation": comments, "inline": review_comments}, limitations=[] if comments_complete and review_comments_complete else ["pagination incomplete"]),
            self._evidence_record("EVD-REVIEW-THREADS", "REVIEW_THREADS", "GitHub GraphQL PullRequest.reviewThreads", {
                "pull_request_number": pr_number,
                "thread_count": len(review_threads),
                "threads": review_threads,
            }, limitations=thread_limitations),
            self._evidence_record(
                "EVD-STABILIZATION",
                "TARGET_STABILIZATION",
                f"final selector re-read for PR #{pr_number}",
                {"initial": initial_selector, "final": final_selector, "stable": target_stable},
                limitations=[] if target_stable else ["PR selector identity moved during evidence collection"],
            ),
        ]
        return finalize_evidence_bundle({
            "schema_version": 2,
            "collected_at_epoch": int(time.time()),
            "target": target,
            "review_intent": request["review_intent"],
            "identity": {"repository_id": str(repo["id"]), "base_ref": pr["base"]["ref"], "base_sha": base_sha, "head_ref": pr["head"]["ref"], "head_sha": head_sha, "merge_base_sha": merge_base_sha, "pr_state": pr.get("state")},
            "freshness": "CURRENT" if target_stable else "STALE",
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

        final_base, _ = self._request(f"/repos/{repo_name}/commits/{base}")
        final_head, _ = self._request(f"/repos/{repo_name}/commits/{head}")
        require(isinstance(final_base, dict), "base-ref stabilization response must be object")
        require(isinstance(final_head, dict), "target-ref stabilization response must be object")
        final_base_sha = final_base.get("sha")
        final_head_sha = final_head.get("sha")
        target_stable = final_base_sha == base_sha and final_head_sha == head_sha
        if not target_stable:
            gaps.append("target_selector_moved_during_collection")

        evidence = self._evidence_record("EVD-COMPARE", "REF_COMPARISON", f"compare {target['base_ref']}...{target['target_ref']}", {
            "status": compare.get("status"), "ahead_by": compare.get("ahead_by"), "behind_by": compare.get("behind_by"),
            "files": [{"filename": item.get("filename"), "status": item.get("status"), "changes": item.get("changes"), "patch": item.get("patch")} for item in files],
        }, limitations=limitations)
        stabilization = self._evidence_record(
            "EVD-STABILIZATION",
            "TARGET_STABILIZATION",
            f"final ref re-resolution for {target['base_ref']}...{target['target_ref']}",
            {
                "initial": {"base_sha": base_sha, "head_sha": head_sha},
                "final": {"base_sha": final_base_sha, "head_sha": final_head_sha},
                "stable": target_stable,
            },
            limitations=[] if target_stable else ["base/target ref identity moved during evidence collection"],
        )
        return finalize_evidence_bundle({
            "schema_version": 2,
            "collected_at_epoch": int(time.time()),
            "target": target,
            "review_intent": request["review_intent"],
            "identity": {"repository_id": str(repo["id"]), "base_ref": target["base_ref"], "base_sha": base_sha, "head_ref": target["target_ref"], "head_sha": head_sha, "merge_base_sha": merge_base_sha},
            "freshness": "CURRENT" if target_stable else "STALE",
            "completeness": {
                "full_coverage": not gaps,
                "material_gaps": sorted(set(gaps)),
                "surfaces": {
                    "target_stabilization": target_stable,
                    "changed_file_inventory": inventory_complete,
                    "diff_content": diff_content_complete,
                },
            },
            "evidence_records": [
                self._evidence_record("EVD-REPO", "REPOSITORY", f"GET /repos/{repo_name}", {"id": repo.get("id"), "full_name": repo.get("full_name")}),
                evidence,
                stabilization,
            ],
        })


    @staticmethod
    def _decode_repository_blob(raw: bytes) -> tuple[str, str | None]:
        if b"\x00" in raw:
            return "UNSUPPORTED_BINARY", None
        try:
            return "TEXT", raw.decode("utf-8")
        except UnicodeDecodeError:
            return "UNSUPPORTED_BINARY", None

    def _fetch_exact_blob(self, repo_name: str, blob_sha: str, expected_size: int) -> bytes:
        payload, _ = self._request(f"/repos/{repo_name}/git/blobs/{blob_sha}")
        require(isinstance(payload, dict), f"blob {blob_sha} response must be an object")
        require(payload.get("sha") == blob_sha, f"blob {blob_sha} response SHA mismatch")
        require(payload.get("encoding") == "base64", f"blob {blob_sha} response encoding must be base64")
        content = payload.get("content")
        require(isinstance(content, str), f"blob {blob_sha} response omitted content")
        try:
            raw = base64.b64decode(content, validate=False)
        except (ValueError, binascii.Error) as exc:
            raise ContractError(f"blob {blob_sha} base64 content is invalid") from exc
        declared_size = payload.get("size")
        require(
            isinstance(declared_size, int) and declared_size == len(raw),
            f"blob {blob_sha} response size does not match decoded content",
        )
        require(declared_size == expected_size, f"blob {blob_sha} size does not match resolved tree")
        return raw

    def _collect_repository_source_content(
        self,
        repo_name: str,
        entries: list[Any],
        *,
        inventory_complete: bool,
    ) -> tuple[list[dict[str, Any]], bool, list[str], list[str]]:
        blobs = sorted(
            [
                item
                for item in entries
                if isinstance(item, dict)
                and item.get("type") == "blob"
                and isinstance(item.get("path"), str)
                and isinstance(item.get("sha"), str)
            ],
            key=lambda item: item["path"],
        )
        gitlinks = sorted(
            [
                item
                for item in entries
                if isinstance(item, dict)
                and item.get("type") == "commit"
                and isinstance(item.get("path"), str)
            ],
            key=lambda item: item["path"],
        )
        results: list[dict[str, Any]] = []
        gaps: list[str] = []
        limitations: list[str] = []
        fetched_bytes = 0

        if gitlinks:
            gaps.append("repository_gitlink_content_uncollected")
            limitations.append(
                f"repository contains {len(gitlinks)} gitlink/submodule entry(s) whose source content is external"
            )
            results.extend(
                {
                    "path": item["path"],
                    "blob_sha": item.get("sha"),
                    "size": item.get("size"),
                    "classification": "EXTERNAL_GITLINK_UNCOLLECTED",
                }
                for item in gitlinks[:20]
            )
            if len(gitlinks) > 20:
                results.append(
                    {
                        "classification": "EXTERNAL_GITLINK_REMAINDER",
                        "remaining_count": len(gitlinks) - 20,
                    }
                )

        for index, item in enumerate(blobs):
            if index >= self.repository_source_max_files:
                remaining = blobs[index:]
                gaps.append("repository_source_file_count_budget_exhausted")
                limitations.append(
                    f"repository source file budget exhausted after {self.repository_source_max_files} blob(s); "
                    f"{len(remaining)} blob(s) remain uncollected"
                )
                results.append(
                    {
                        "classification": "FILE_COUNT_BUDGET_BLOCKED_REMAINDER",
                        "remaining_count": len(remaining),
                        "first_paths": [entry["path"] for entry in remaining[:20]],
                    }
                )
                break

            path = item["path"]
            blob_sha = item["sha"]
            size = item.get("size")
            if not isinstance(size, int) or size < 0:
                gaps.append("repository_source_blob_size_unknown")
                limitations.append(f"{path}: resolved tree omitted a usable blob size")
                results.append(
                    {
                        "path": path,
                        "blob_sha": blob_sha,
                        "size": size,
                        "classification": "SIZE_UNKNOWN_UNCOLLECTED",
                    }
                )
                continue
            if size > self.repository_source_max_blob_bytes:
                gaps.append("repository_source_blob_oversized")
                limitations.append(
                    f"{path}: {size} bytes exceeds per-blob source limit {self.repository_source_max_blob_bytes}"
                )
                results.append(
                    {
                        "path": path,
                        "blob_sha": blob_sha,
                        "size": size,
                        "classification": "OVERSIZED_UNCOLLECTED",
                    }
                )
                continue
            if fetched_bytes + size > self.repository_source_max_total_bytes:
                gaps.append("repository_source_byte_budget_exhausted")
                limitations.append(
                    f"{path}: collecting {size} bytes would exceed total source limit "
                    f"{self.repository_source_max_total_bytes}"
                )
                results.append(
                    {
                        "path": path,
                        "blob_sha": blob_sha,
                        "size": size,
                        "classification": "BYTE_BUDGET_BLOCKED",
                    }
                )
                continue
            try:
                raw = self._fetch_exact_blob(repo_name, blob_sha, size)
            except ContractError as exc:
                gaps.append("repository_source_blob_unavailable")
                limitations.append(f"{path}: {exc}")
                results.append(
                    {
                        "path": path,
                        "blob_sha": blob_sha,
                        "size": size,
                        "classification": "UNAVAILABLE",
                    }
                )
                continue

            fetched_bytes += len(raw)
            classification, text = self._decode_repository_blob(raw)
            result = {
                "path": path,
                "blob_sha": blob_sha,
                "size": size,
                "classification": classification,
            }
            if classification == "TEXT":
                result["content"] = text
            else:
                result["limitation"] = (
                    "exact blob bytes were fetched and classified as binary/non-UTF-8; "
                    "content was not represented as semantically reviewed text"
                )
                limitations.append(
                    f"{path}: exact blob classified as unsupported binary/non-UTF-8 content"
                )
            results.append(result)

        if gaps:
            gaps.append("repository_source_content_incomplete")
        source_complete = inventory_complete and not gaps
        return results, source_complete, sorted(set(gaps)), limitations


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
        require(isinstance(entries, list), "tree response entries must be a list")
        inventory_complete = not truncated
        source_items, source_complete, source_gaps, source_limitations = (
            self._collect_repository_source_content(
                repo_name,
                entries,
                inventory_complete=inventory_complete,
            )
        )

        final_commit, _ = self._request(f"/repos/{repo_name}/commits/{ref}")
        require(isinstance(final_commit, dict), "repository-ref stabilization response must be object")
        final_head_sha = final_commit.get("sha")
        target_stable = final_head_sha == head_sha
        gaps = list(source_gaps)
        if truncated:
            gaps.append("recursive_tree_truncated")
        if not target_stable:
            gaps.append("target_selector_moved_during_collection")
        gaps = sorted(set(gaps))

        return finalize_evidence_bundle({
            "schema_version": 2,
            "collected_at_epoch": int(time.time()),
            "target": target,
            "review_intent": request["review_intent"],
            "identity": {
                "repository_id": str(repo["id"]),
                "head_ref": requested_ref,
                "head_sha": head_sha,
                "base_sha": None,
                "merge_base_sha": None,
            },
            "freshness": "CURRENT" if target_stable else "STALE",
            "completeness": {
                "full_coverage": inventory_complete and source_complete and target_stable and not gaps,
                "material_gaps": gaps,
                "surfaces": {
                    "target_stabilization": target_stable,
                    "repository_tree_inventory": inventory_complete,
                    "repository_source_content": source_complete,
                },
            },
            "evidence_records": [
                self._evidence_record(
                    "EVD-REPO",
                    "REPOSITORY",
                    f"GET /repos/{repo_name}",
                    {
                        "id": repo.get("id"),
                        "full_name": repo.get("full_name"),
                        "default_branch": repo.get("default_branch"),
                    },
                ),
                self._evidence_record(
                    "EVD-SNAPSHOT",
                    "REPOSITORY_SNAPSHOT",
                    f"commit/tree at {requested_ref}",
                    {
                        "commit_sha": head_sha,
                        "tree_sha": tree_sha,
                        "paths": [
                            {
                                "path": item.get("path"),
                                "type": item.get("type"),
                                "sha": item.get("sha"),
                                "size": item.get("size"),
                            }
                            for item in entries
                        ],
                    },
                    limitations=["recursive tree truncated"] if truncated else [],
                ),
                self._evidence_record(
                    "EVD-SOURCE",
                    "REPOSITORY_SOURCE_CONTENT",
                    f"exact Git blobs from tree {tree_sha}",
                    {
                        "source_file_limit": self.repository_source_max_files,
                        "source_total_byte_limit": self.repository_source_max_total_bytes,
                        "source_blob_byte_limit": self.repository_source_max_blob_bytes,
                        "items": source_items,
                    },
                    limitations=source_limitations,
                ),
                self._evidence_record(
                    "EVD-STABILIZATION",
                    "TARGET_STABILIZATION",
                    f"final ref re-resolution for {requested_ref}",
                    {
                        "initial": {"head_sha": head_sha},
                        "final": {"head_sha": final_head_sha},
                        "stable": target_stable,
                    },
                    limitations=[] if target_stable else ["repository ref identity moved during evidence collection"],
                ),
            ],
        })
