from __future__ import annotations

import base64
import copy
import unittest
from unittest.mock import patch

from engineering_compass.github_evidence import GitHubEvidenceCollector
from engineering_compass.model import ContractError, expected_target_binding
from engineering_compass.projection import project_action


def clone(value):
    return copy.deepcopy(value)


class RepositoryEvidenceCompletenessTests(unittest.TestCase):
    def _collect_repository(
        self,
        entries,
        blobs,
        *,
        truncated=False,
        collector_kwargs=None,
    ):
        collector = GitHubEvidenceCollector(token="x", **(collector_kwargs or {}))
        commit = {"sha": "a" * 40, "commit": {"tree": {"sha": "c" * 40}}}
        tree = {"truncated": truncated, "tree": entries}

        def request(path, **_kwargs):
            if path.startswith("/repos/acme/example/commits/"):
                return commit, {}
            if "/git/trees/" in path:
                return tree, {}
            if "/git/blobs/" in path:
                sha = path.rsplit("/", 1)[-1]
                if sha not in blobs:
                    raise ContractError(f"blob unavailable: {sha}")
                raw = blobs[sha]
                return {
                    "sha": sha,
                    "encoding": "base64",
                    "content": base64.b64encode(raw).decode("ascii"),
                    "size": len(raw),
                }, {}
            raise AssertionError(f"unexpected request path: {path}")

        with patch.object(
            collector,
            "_repo",
            return_value={"id": 1, "full_name": "acme/example", "default_branch": "main"},
        ), patch.object(collector, "_request", side_effect=request):
            return collector.collect(
                {
                    "target": {"kind": "REPOSITORY_SCOPE", "repository": "acme/example", "ref": "main"},
                    "review_intent": "repository review",
                }
            )

    @staticmethod
    def _blob_entry(path, sha, raw):
        return {"path": path, "type": "blob", "sha": sha, "size": len(raw)}

    def test_tree_only_inventory_cannot_claim_semantic_full_coverage(self):
        raw = b"print('hello')\n"
        entries = [self._blob_entry("app.py", "1" * 40, raw)]
        evidence = self._collect_repository(
            entries,
            {"1" * 40: raw},
            collector_kwargs={"repository_source_max_files": 0},
        )
        self.assertTrue(evidence["completeness"]["surfaces"]["repository_tree_inventory"])
        self.assertFalse(evidence["completeness"]["surfaces"]["repository_source_content"])
        self.assertFalse(evidence["completeness"]["full_coverage"])
        self.assertIn(
            "repository_source_content_incomplete",
            evidence["completeness"]["material_gaps"],
        )

    def test_small_repository_binds_complete_exact_blob_source_content(self):
        raw_a = b"print('hello')\n"
        raw_b = b'{"enabled": true}\n'
        entries = [
            self._blob_entry("app.py", "1" * 40, raw_a),
            self._blob_entry("config.json", "2" * 40, raw_b),
        ]
        evidence = self._collect_repository(
            entries,
            {"1" * 40: raw_a, "2" * 40: raw_b},
        )
        self.assertTrue(evidence["completeness"]["surfaces"]["repository_tree_inventory"])
        self.assertTrue(evidence["completeness"]["surfaces"]["repository_source_content"])
        self.assertTrue(evidence["completeness"]["full_coverage"])
        self.assertEqual(evidence["completeness"]["material_gaps"], [])

        source = next(item for item in evidence["evidence_records"] if item["evidence_id"] == "EVD-SOURCE")
        items = source["payload"]["items"]
        self.assertEqual([item["path"] for item in items], ["app.py", "config.json"])
        self.assertEqual(items[0]["blob_sha"], "1" * 40)
        self.assertEqual(items[0]["classification"], "TEXT")
        self.assertEqual(items[0]["content"], raw_a.decode("utf-8"))

    def test_unavailable_oversized_or_budget_blocked_blob_fails_closed(self):
        scenarios = [
            (
                "unavailable",
                {"repository_source_max_blob_bytes": 1024},
                {},
                "repository_source_blob_unavailable",
            ),
            (
                "oversized",
                {"repository_source_max_blob_bytes": 3},
                {"1" * 40: b"four"},
                "repository_source_blob_oversized",
            ),
            (
                "budget",
                {"repository_source_max_total_bytes": 3},
                {"1" * 40: b"four"},
                "repository_source_byte_budget_exhausted",
            ),
        ]
        for name, limits, blobs, expected_gap in scenarios:
            with self.subTest(name=name):
                raw = b"four"
                entries = [self._blob_entry("app.py", "1" * 40, raw)]
                evidence = self._collect_repository(entries, blobs, collector_kwargs=limits)
                self.assertFalse(evidence["completeness"]["surfaces"]["repository_source_content"])
                self.assertFalse(evidence["completeness"]["full_coverage"])
                self.assertIn(expected_gap, evidence["completeness"]["material_gaps"])
                source = next(
                    item for item in evidence["evidence_records"] if item["evidence_id"] == "EVD-SOURCE"
                )
                self.assertTrue(source["limitations"])

    def test_changed_blob_same_path_changes_digest_and_stales_old_assessment(self):
        raw_a = b"value = 1\n"
        raw_b = b"value = 2\n"
        evidence_a = self._collect_repository(
            [self._blob_entry("app.py", "1" * 40, raw_a)],
            {"1" * 40: raw_a},
        )
        evidence_b = self._collect_repository(
            [self._blob_entry("app.py", "2" * 40, raw_b)],
            {"2" * 40: raw_b},
        )
        self.assertNotEqual(evidence_a["evidence_digest"], evidence_b["evidence_digest"])

        assessment = {
            "assessment_version": 2,
            "target_binding": expected_target_binding(evidence_a),
            "method_coverage": [],
            "findings": [],
            "root_cause_groups": [],
            "unverified_areas": [],
            "owner_policy_decision_required": False,
            "specialist_review_required": False,
            "stop_reason": "No material finding in the first exact snapshot.",
        }
        self.assertEqual(project_action(evidence_b, assessment)["action"], "RERUN_REVIEW")

    def test_binary_blob_is_truthfully_classified_not_semantically_claimed_as_text(self):
        raw = b"\x00\xff\x10binary"
        evidence = self._collect_repository(
            [self._blob_entry("asset.bin", "1" * 40, raw)],
            {"1" * 40: raw},
        )
        source = next(item for item in evidence["evidence_records"] if item["evidence_id"] == "EVD-SOURCE")
        item = source["payload"]["items"][0]
        self.assertEqual(item["classification"], "UNSUPPORTED_BINARY")
        self.assertNotIn("content", item)
        self.assertIn("not represented as semantically reviewed text", item["limitation"])
        self.assertTrue(source["limitations"])

    def test_selected_method_deviation_tree_only_formula_would_fail(self):
        raw = b"x = 1\n"
        evidence = self._collect_repository(
            [self._blob_entry("app.py", "1" * 40, raw)],
            {"1" * 40: raw},
            collector_kwargs={"repository_source_max_total_bytes": 0},
        )
        self.assertTrue(evidence["completeness"]["surfaces"]["repository_tree_inventory"])
        self.assertFalse(evidence["completeness"]["surfaces"]["repository_source_content"])
        self.assertFalse(evidence["completeness"]["full_coverage"])


class PullRequestDecisionSurfaceTests(unittest.TestCase):
    @staticmethod
    def _thread(
        thread_id,
        *,
        resolved=False,
        outdated=False,
        path="app.py",
        line=10,
        comments=None,
    ):
        return {
            "id": thread_id,
            "isResolved": resolved,
            "isOutdated": outdated,
            "path": path,
            "line": line,
            "originalLine": line,
            "startLine": None,
            "originalStartLine": None,
            "diffSide": "RIGHT",
            "startDiffSide": None,
            "subjectType": "LINE",
            "comments": comments or [],
            "comments_complete": True,
        }

    def _collect_pr(
        self,
        *,
        checks=None,
        statuses=None,
        statuses_complete=True,
        status_limitations=None,
        threads=None,
        threads_complete=True,
        thread_limitations=None,
        expected_changed_files=1,
        files=None,
    ):
        collector = GitHubEvidenceCollector(token="x")
        files = files if files is not None else [
            {"filename": "app.py", "status": "modified", "patch": "@@"}
        ]
        pr = {
            "number": 1,
            "state": "open",
            "draft": False,
            "changed_files": expected_changed_files,
            "base": {"ref": "main", "sha": "b" * 40},
            "head": {"ref": "feat", "sha": "a" * 40},
        }
        compare = {"merge_base_commit": {"sha": "c" * 40}}
        check_payload = {"check_runs": checks or [], "total_count": len(checks or [])}

        def paginate(path, **_kwargs):
            if path.endswith("/files"):
                return files, True
            return [], True

        def request(path, **_kwargs):
            if path.endswith("/pulls/1"):
                return pr, {}
            if "/compare/" in path:
                return compare, {}
            if "/check-runs" in path:
                return check_payload, {}
            raise AssertionError(f"unexpected request path: {path}")

        with patch.object(
            collector,
            "_repo",
            return_value={"id": 1, "full_name": "acme/example", "default_branch": "main"},
        ), patch.object(collector, "_paginate", side_effect=paginate), patch.object(
            collector, "_request", side_effect=request
        ), patch.object(
            collector,
            "_collect_commit_statuses",
            return_value=(
                statuses or [],
                statuses_complete,
                status_limitations or [],
            ),
        ), patch.object(
            collector,
            "_collect_review_threads",
            return_value=(
                threads or [],
                threads_complete,
                thread_limitations or [],
            ),
        ):
            return collector.collect(
                {
                    "target": {"kind": "PR_SCOPE", "repository": "acme/example", "pr_number": 1},
                    "review_intent": "PR review",
                }
            )

    def test_successful_checks_do_not_hide_failing_commit_status(self):
        checks = [
            {
                "name": "tests",
                "status": "completed",
                "conclusion": "success",
                "app": {"id": 7, "slug": "actions"},
                "details_url": "https://example.test/check",
                "head_sha": "a" * 40,
            }
        ]
        statuses = [
            {
                "context": "legacy-ci",
                "state": "failure",
                "description": "legacy build failed",
                "target_url": "https://example.test/status",
                "creator": {"login": "legacy-bot", "id": 9},
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:01:00Z",
            }
        ]
        evidence = self._collect_pr(checks=checks, statuses=statuses)
        check_record = next(
            item for item in evidence["evidence_records"] if item["evidence_id"] == "EVD-CHECKS"
        )
        status_record = next(
            item for item in evidence["evidence_records"] if item["evidence_id"] == "EVD-STATUSES"
        )
        self.assertEqual(check_record["payload"][0]["conclusion"], "success")
        self.assertEqual(status_record["payload"]["statuses"][0]["state"], "failure")
        self.assertEqual(
            status_record["payload"]["statuses"][0]["creator"]["login"],
            "legacy-bot",
        )
        self.assertTrue(evidence["completeness"]["surfaces"]["checks"])
        self.assertTrue(evidence["completeness"]["surfaces"]["commit_statuses"])

    def test_zero_status_contexts_are_proven_by_empty_list_not_aggregate_pending(self):
        evidence = self._collect_pr(statuses=[])
        status_record = next(
            item for item in evidence["evidence_records"] if item["evidence_id"] == "EVD-STATUSES"
        )
        self.assertEqual(status_record["payload"]["status_count"], 0)
        self.assertEqual(status_record["payload"]["statuses"], [])
        self.assertTrue(evidence["completeness"]["surfaces"]["commit_statuses"])

    def test_unresolved_review_thread_is_authoritatively_visible(self):
        thread = self._thread(
            "T1",
            resolved=False,
            comments=[{"id": "C1", "body": "Please fix", "author": {"login": "reviewer"}}],
        )
        evidence = self._collect_pr(threads=[thread])
        record = next(
            item for item in evidence["evidence_records"]
            if item["evidence_id"] == "EVD-REVIEW-THREADS"
        )
        self.assertFalse(record["payload"]["threads"][0]["isResolved"])
        self.assertTrue(evidence["completeness"]["surfaces"]["review_threads"])

    def test_resolved_and_outdated_thread_states_remain_independent(self):
        evidence = self._collect_pr(
            threads=[
                self._thread("T1", resolved=True, outdated=False),
                self._thread("T2", resolved=False, outdated=True),
            ]
        )
        record = next(
            item for item in evidence["evidence_records"]
            if item["evidence_id"] == "EVD-REVIEW-THREADS"
        )
        states = {
            item["id"]: (item["isResolved"], item["isOutdated"])
            for item in record["payload"]["threads"]
        }
        self.assertEqual(states["T1"], (True, False))
        self.assertEqual(states["T2"], (False, True))

    def test_thread_api_unavailable_or_incomplete_fails_pr_coverage(self):
        for name, limitation in [
            ("auth", "GitHub GraphQL HTTP 403"),
            ("pagination", "review-thread pagination limit reached"),
        ]:
            with self.subTest(name=name):
                evidence = self._collect_pr(
                    threads_complete=False,
                    thread_limitations=[limitation],
                )
                self.assertFalse(evidence["completeness"]["surfaces"]["review_threads"])
                self.assertFalse(evidence["completeness"]["full_coverage"])
                self.assertIn(
                    "pr_review_threads_incomplete",
                    evidence["completeness"]["material_gaps"],
                )
                record = next(
                    item for item in evidence["evidence_records"]
                    if item["evidence_id"] == "EVD-REVIEW-THREADS"
                )
                self.assertIn(limitation, record["limitations"])

    def test_positive_control_proven_empty_status_and_thread_surfaces(self):
        evidence = self._collect_pr(statuses=[], threads=[])
        self.assertTrue(evidence["completeness"]["surfaces"]["commit_statuses"])
        self.assertTrue(evidence["completeness"]["surfaces"]["review_threads"])
        self.assertTrue(evidence["completeness"]["full_coverage"])

    def test_checks_and_inline_comments_alone_cannot_prove_pr_completeness(self):
        evidence = self._collect_pr(
            checks=[
                {
                    "name": "tests",
                    "status": "completed",
                    "conclusion": "success",
                    "app": {"id": 7, "slug": "actions"},
                    "details_url": None,
                    "head_sha": "a" * 40,
                }
            ],
            statuses_complete=False,
            status_limitations=["statuses not collected"],
            threads_complete=False,
            thread_limitations=["threads not collected"],
        )
        self.assertTrue(evidence["completeness"]["surfaces"]["checks"])
        self.assertFalse(evidence["completeness"]["surfaces"]["commit_statuses"])
        self.assertFalse(evidence["completeness"]["surfaces"]["review_threads"])
        self.assertFalse(evidence["completeness"]["full_coverage"])

    def test_pr_3000_file_ceiling_remains_fail_closed(self):
        files = [
            {"filename": f"f{i}.py", "status": "modified", "patch": "@@"}
            for i in range(3000)
        ]
        evidence = self._collect_pr(
            expected_changed_files=3001,
            files=files,
        )
        self.assertFalse(evidence["completeness"]["surfaces"]["changed_file_inventory"])
        self.assertFalse(evidence["completeness"]["full_coverage"])
        self.assertIn(
            "pr_changed_files_cap_exceeded",
            evidence["completeness"]["material_gaps"],
        )


class ReviewThreadPaginationTests(unittest.TestCase):
    @staticmethod
    def _comment(comment_id, body):
        return {
            "id": comment_id,
            "body": body,
            "author": {"login": "reviewer"},
            "authorAssociation": "MEMBER",
            "createdAt": "2026-01-01T00:00:00Z",
            "lastEditedAt": None,
            "url": f"https://example.test/{comment_id}",
        }

    def test_review_threads_and_nested_comments_are_fully_paginated(self):
        collector = GitHubEvidenceCollector(token="x")
        page_one = {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "nodes": [
                            {
                                "id": "T1",
                                "isResolved": False,
                                "isOutdated": False,
                                "path": "app.py",
                                "line": 10,
                                "originalLine": 10,
                                "startLine": None,
                                "originalStartLine": None,
                                "diffSide": "RIGHT",
                                "startDiffSide": None,
                                "subjectType": "LINE",
                                "comments": {
                                    "nodes": [self._comment("C1", "one")],
                                    "pageInfo": {"hasNextPage": True, "endCursor": "C-CURSOR"},
                                },
                            }
                        ],
                        "pageInfo": {"hasNextPage": True, "endCursor": "T-CURSOR"},
                    }
                }
            }
        }
        comment_page = {
            "node": {
                "comments": {
                    "nodes": [self._comment("C2", "two")],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }
        page_two = {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "nodes": [
                            {
                                "id": "T2",
                                "isResolved": True,
                                "isOutdated": True,
                                "path": "old.py",
                                "line": None,
                                "originalLine": 5,
                                "startLine": None,
                                "originalStartLine": None,
                                "diffSide": "RIGHT",
                                "startDiffSide": None,
                                "subjectType": "LINE",
                                "comments": {
                                    "nodes": [],
                                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                                },
                            }
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }
                }
            }
        }
        with patch.object(
            collector,
            "_graphql_request",
            side_effect=[page_one, comment_page, page_two],
        ):
            threads, complete, limitations = collector._collect_review_threads("acme/example", 1)

        self.assertTrue(complete)
        self.assertEqual(limitations, [])
        self.assertEqual([item["id"] for item in threads], ["T1", "T2"])
        self.assertEqual(
            [comment["id"] for comment in threads[0]["comments"]],
            ["C1", "C2"],
        )
        self.assertTrue(threads[0]["comments_complete"])

    def test_review_thread_auth_failure_is_incomplete_not_empty_success(self):
        collector = GitHubEvidenceCollector(token="x")
        with patch.object(
            collector,
            "_graphql_request",
            side_effect=ContractError("GitHub GraphQL HTTP 403"),
        ):
            threads, complete, limitations = collector._collect_review_threads("acme/example", 1)
        self.assertEqual(threads, [])
        self.assertFalse(complete)
        self.assertTrue(limitations)

    def test_review_thread_pagination_limit_is_incomplete(self):
        collector = GitHubEvidenceCollector(token="x")
        page = {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "nodes": [],
                        "pageInfo": {"hasNextPage": True, "endCursor": "NEXT"},
                    }
                }
            }
        }
        with patch("engineering_compass.github_evidence.REVIEW_THREAD_MAX_PAGES", 1), patch.object(
            collector,
            "_graphql_request",
            return_value=page,
        ):
            threads, complete, limitations = collector._collect_review_threads("acme/example", 1)
        self.assertEqual(threads, [])
        self.assertFalse(complete)
        self.assertIn("pagination limit", limitations[0])


class CommitStatusCollectionTests(unittest.TestCase):
    def test_status_endpoint_is_paginated_independently_from_checks(self):
        collector = GitHubEvidenceCollector(token="x")
        statuses = [
            {
                "context": "legacy",
                "state": "success",
                "description": "ok",
                "target_url": None,
                "creator": {"login": "bot", "id": 1},
            }
        ]
        with patch.object(collector, "_paginate", return_value=(statuses, True)) as paginate:
            actual, complete, limitations = collector._collect_commit_statuses(
                "acme/example",
                "a" * 40,
            )
        self.assertEqual(actual, statuses)
        self.assertTrue(complete)
        self.assertEqual(limitations, [])
        self.assertIn("/statuses", paginate.call_args.args[0])
        self.assertNotIn("/check-runs", paginate.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
