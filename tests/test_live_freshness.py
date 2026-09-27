from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import engineering_compass
from engineering_compass.cli import main as cli_main
from engineering_compass.github_evidence import GitHubEvidenceCollector
from engineering_compass.model import (
    ContractError,
    expected_target_binding,
    finalize_evidence_bundle,
)
from engineering_compass.projection import _project_action_current, project_action
from engineering_compass.prompt_pipeline import build_prompt_pipeline_intake

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(name: str) -> dict:
    return json.loads((ROOT / "fixtures" / "runtime" / name).read_text(encoding="utf-8"))


def clone(value):
    return copy.deepcopy(value)


class StaticCollector:
    def __init__(self, evidence: dict):
        self.evidence = evidence
        self.requests: list[dict] = []

    def collect(self, request: dict) -> dict:
        self.requests.append(clone(request))
        return clone(self.evidence)


class FailingCollector:
    def collect(self, request: dict) -> dict:
        raise ContractError("live GitHub freshness unavailable")


def empty_assessment(evidence: dict) -> dict:
    return {
        "assessment_version": 2,
        "target_binding": expected_target_binding(evidence),
        "method_coverage": [],
        "findings": [],
        "root_cause_groups": [],
        "unverified_areas": [],
        "owner_policy_decision_required": False,
        "specialist_review_required": False,
        "stop_reason": "No material repair obligation.",
    }


def repository_evidence(head_sha: str) -> dict:
    return finalize_evidence_bundle({
        "schema_version": 2,
        "target": {"kind": "REPOSITORY_SCOPE", "repository": "acme/example", "ref": "main"},
        "review_intent": "Repository review",
        "identity": {
            "repository_id": "123",
            "head_ref": "main",
            "head_sha": head_sha,
            "base_sha": None,
            "merge_base_sha": None,
        },
        "freshness": "CURRENT",
        "completeness": {
            "full_coverage": True,
            "material_gaps": [],
            "surfaces": {
                "target_stabilization": True,
                "repository_tree_inventory": True,
                "repository_source_content": True,
            },
        },
        "evidence_records": [
            {
                "evidence_id": "EVD-SNAPSHOT",
                "kind": "REPOSITORY_SNAPSHOT",
                "source": "test",
                "payload": {"head_sha": head_sha},
                "limitations": [],
            }
        ],
    })


def ref_delta_evidence(base_sha: str, head_sha: str) -> dict:
    return finalize_evidence_bundle({
        "schema_version": 2,
        "target": {
            "kind": "REF_DELTA_SCOPE",
            "repository": "acme/example",
            "base_ref": "main",
            "target_ref": "feature",
        },
        "review_intent": "Ref delta review",
        "identity": {
            "repository_id": "123",
            "base_ref": "main",
            "base_sha": base_sha,
            "head_ref": "feature",
            "head_sha": head_sha,
            "merge_base_sha": "c" * 40,
        },
        "freshness": "CURRENT",
        "completeness": {
            "full_coverage": True,
            "material_gaps": [],
            "surfaces": {
                "target_stabilization": True,
                "changed_file_inventory": True,
                "diff_content": True,
            },
        },
        "evidence_records": [
            {
                "evidence_id": "EVD-COMPARE",
                "kind": "REF_COMPARISON",
                "source": "test",
                "payload": {"base_sha": base_sha, "head_sha": head_sha},
                "limitations": [],
            }
        ],
    })


class LiveFreshnessAuthorityTests(unittest.TestCase):
    def test_pr_head_move_routes_rerun_review_even_with_same_effective_diff(self):
        fixture = load_fixture("repair-full.json")
        reviewed = fixture["evidence"]
        live = clone(reviewed)
        live["identity"]["head_sha"] = "f" * 40
        finalize_evidence_bundle(live)

        # The deterministic old behavior would still authorize the persisted snapshot.
        self.assertEqual(
            _project_action_current(reviewed, fixture["assessment"])["action"],
            "IMPLEMENT_REPAIR",
        )
        projection = project_action(
            reviewed,
            fixture["assessment"],
            collector=StaticCollector(live),
        )
        self.assertEqual(projection["action"], "RERUN_REVIEW")
        self.assertFalse(projection["may_modify_code"])

    def test_same_head_material_pr_surface_drift_routes_rerun_review(self):
        fixture = load_fixture("repair-full.json")
        reviewed = clone(fixture["evidence"])
        reviewed["evidence_records"].extend([
            {"evidence_id": "EVD-CHECKS", "kind": "CHECK_RUNS", "source": "checks", "payload": {"state": "success"}, "limitations": []},
            {"evidence_id": "EVD-STATUSES", "kind": "COMMIT_STATUSES", "source": "statuses", "payload": {"state": "success"}, "limitations": []},
            {"evidence_id": "EVD-REVIEWS", "kind": "REVIEWS", "source": "reviews", "payload": {"state": "APPROVED"}, "limitations": []},
            {"evidence_id": "EVD-COMMENTS", "kind": "COMMENTS", "source": "comments", "payload": {"body": "old"}, "limitations": []},
            {"evidence_id": "EVD-REVIEW-THREADS", "kind": "REVIEW_THREADS", "source": "threads", "payload": {"isResolved": True}, "limitations": []},
        ])
        finalize_evidence_bundle(reviewed)
        assessment = clone(fixture["assessment"])
        assessment["target_binding"] = expected_target_binding(reviewed)

        for evidence_id, payload in [
            ("EVD-CHECKS", {"state": "failure"}),
            ("EVD-STATUSES", {"state": "failure"}),
            ("EVD-REVIEWS", {"state": "CHANGES_REQUESTED"}),
            ("EVD-COMMENTS", {"body": "new"}),
            ("EVD-REVIEW-THREADS", {"isResolved": False}),
        ]:
            with self.subTest(evidence_id=evidence_id):
                live = clone(reviewed)
                record = next(item for item in live["evidence_records"] if item["evidence_id"] == evidence_id)
                record["payload"] = payload
                finalize_evidence_bundle(live)
                self.assertEqual(live["identity"]["head_sha"], reviewed["identity"]["head_sha"])
                projection = project_action(reviewed, assessment, collector=StaticCollector(live))
                self.assertEqual(projection["action"], "RERUN_REVIEW")
                self.assertFalse(projection["may_modify_code"])

    def test_repository_symbolic_ref_move_routes_rerun_review(self):
        reviewed = repository_evidence("a" * 40)
        assessment = empty_assessment(reviewed)
        live = repository_evidence("b" * 40)
        projection = project_action(reviewed, assessment, collector=StaticCollector(live))
        self.assertEqual(projection["action"], "RERUN_REVIEW")
        self.assertFalse(projection["may_modify_code"])

    def test_ref_delta_base_or_target_move_routes_rerun_review(self):
        reviewed = ref_delta_evidence("a" * 40, "b" * 40)
        assessment = empty_assessment(reviewed)
        for base_sha, head_sha in [("d" * 40, "b" * 40), ("a" * 40, "e" * 40)]:
            with self.subTest(base_sha=base_sha, head_sha=head_sha):
                live = ref_delta_evidence(base_sha, head_sha)
                projection = project_action(reviewed, assessment, collector=StaticCollector(live))
                self.assertEqual(projection["action"], "RERUN_REVIEW")
                self.assertFalse(projection["may_modify_code"])

    def test_live_revalidation_failure_emits_no_projection_or_handoff_authority(self):
        fixture = load_fixture("repair-full.json")
        with self.assertRaises(ContractError):
            project_action(
                fixture["evidence"],
                fixture["assessment"],
                collector=FailingCollector(),
            )
        with self.assertRaises(ContractError):
            build_prompt_pipeline_intake(
                fixture["evidence"],
                fixture["assessment"],
                collector=FailingCollector(),
            )

    def test_unchanged_live_evidence_preserves_root_complete_implementation(self):
        fixture = load_fixture("repair-full.json")
        collector = StaticCollector(fixture["evidence"])
        projection = project_action(
            fixture["evidence"],
            fixture["assessment"],
            collector=collector,
        )
        self.assertEqual(projection["action"], "IMPLEMENT_REPAIR")
        self.assertTrue(projection["may_modify_code"])
        self.assertEqual(
            collector.requests[0],
            {
                "target": fixture["evidence"]["target"],
                "review_intent": fixture["evidence"]["review_intent"],
            },
        )

        intake = build_prompt_pipeline_intake(
            fixture["evidence"],
            fixture["assessment"],
            collector=StaticCollector(fixture["evidence"]),
        )
        self.assertTrue(intake["potential_downstream_execution"])
        self.assertEqual(intake["requested_actions"], ["IMPLEMENT_REPAIR"])

    def test_moved_live_evidence_can_only_build_nonmodifying_rerun_handoff(self):
        fixture = load_fixture("repair-full.json")
        live = clone(fixture["evidence"])
        live["identity"]["head_sha"] = "f" * 40
        finalize_evidence_bundle(live)
        intake = build_prompt_pipeline_intake(
            fixture["evidence"],
            fixture["assessment"],
            collector=StaticCollector(live),
        )
        self.assertFalse(intake["potential_downstream_execution"])
        self.assertEqual(intake["requested_actions"], ["RERUN_REVIEW"])
        self.assertIn("Code modification authorization: NONE.", intake["request"])

    def test_package_exports_are_live_gated(self):
        fixture = load_fixture("repair-full.json")
        with self.assertRaises(ContractError):
            engineering_compass.project_action(
                fixture["evidence"],
                fixture["assessment"],
                collector=FailingCollector(),
            )
        with self.assertRaises(ContractError):
            engineering_compass.build_prompt_pipeline_intake(
                fixture["evidence"],
                fixture["assessment"],
                collector=FailingCollector(),
            )

    def test_cli_project_and_prompt_handoff_fail_closed_without_live_gate(self):
        fixture = load_fixture("repair-full.json")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence_path = root / "evidence.json"
            assessment_path = root / "assessment.json"
            evidence_path.write_text(json.dumps(fixture["evidence"]), encoding="utf-8")
            assessment_path.write_text(json.dumps(fixture["assessment"]), encoding="utf-8")

            with patch(
                "engineering_compass.projection.GitHubEvidenceCollector",
                return_value=FailingCollector(),
            ):
                project_out = root / "projection.json"
                self.assertEqual(
                    cli_main([
                        "project",
                        "--evidence", str(evidence_path),
                        "--assessment", str(assessment_path),
                        "--out", str(project_out),
                    ]),
                    2,
                )
                self.assertFalse(project_out.exists())

                handoff_out = root / "intake.json"
                self.assertEqual(
                    cli_main([
                        "prompt-handoff",
                        "--evidence", str(evidence_path),
                        "--assessment", str(assessment_path),
                        "--out", str(handoff_out),
                    ]),
                    2,
                )
                self.assertFalse(handoff_out.exists())


class CollectionStabilizationTests(unittest.TestCase):
    def test_pr_head_move_during_collection_marks_bundle_stale_even_if_diff_is_same(self):
        collector = GitHubEvidenceCollector(token="x")
        initial_pr = {
            "number": 1,
            "state": "open",
            "draft": False,
            "changed_files": 1,
            "base": {"ref": "main", "sha": "b" * 40},
            "head": {"ref": "feature", "sha": "a" * 40},
        }
        final_pr = clone(initial_pr)
        final_pr["head"]["sha"] = "d" * 40
        compare = {"merge_base_commit": {"sha": "c" * 40}}
        checks = {"check_runs": [], "total_count": 0}

        with patch.object(
            collector,
            "_repo",
            return_value={"id": 1, "full_name": "acme/example", "default_branch": "main"},
        ), patch.object(
            collector,
            "_paginate",
            side_effect=[
                ([{"filename": "app.py", "status": "modified", "patch": "@@"}], True),
                ([], True),
                ([], True),
                ([], True),
            ],
        ), patch.object(
            collector,
            "_collect_commit_statuses",
            return_value=([], True, []),
        ), patch.object(
            collector,
            "_collect_review_threads",
            return_value=([], True, []),
        ), patch.object(
            collector,
            "_request",
            side_effect=[(initial_pr, {}), (compare, {}), (checks, {}), (final_pr, {})],
        ):
            evidence = collector.collect({
                "target": {"kind": "PR_SCOPE", "repository": "acme/example", "pr_number": 1},
                "review_intent": "review",
            })

        self.assertEqual(evidence["freshness"], "STALE")
        self.assertFalse(evidence["completeness"]["surfaces"]["target_stabilization"])
        self.assertFalse(evidence["completeness"]["full_coverage"])
        self.assertIn(
            "target_selector_moved_during_collection",
            evidence["completeness"]["material_gaps"],
        )

    def test_ref_delta_move_during_collection_marks_bundle_stale(self):
        collector = GitHubEvidenceCollector(token="x")
        compare = {
            "status": "ahead",
            "base_commit": {"sha": "a" * 40},
            "head_commit": {"sha": "b" * 40},
            "merge_base_commit": {"sha": "c" * 40},
            "files": [],
        }
        final_base = {"sha": "d" * 40}
        final_head = {"sha": "b" * 40}
        with patch.object(
            collector,
            "_repo",
            return_value={"id": 1, "full_name": "acme/example"},
        ), patch.object(
            collector,
            "_request",
            side_effect=[(compare, {}), (final_base, {}), (final_head, {})],
        ):
            evidence = collector.collect({
                "target": {
                    "kind": "REF_DELTA_SCOPE",
                    "repository": "acme/example",
                    "base_ref": "main",
                    "target_ref": "feature",
                },
                "review_intent": "review",
            })
        self.assertEqual(evidence["freshness"], "STALE")
        self.assertFalse(evidence["completeness"]["surfaces"]["target_stabilization"])
        self.assertIn(
            "target_selector_moved_during_collection",
            evidence["completeness"]["material_gaps"],
        )

    def test_repository_ref_move_during_collection_marks_bundle_stale(self):
        collector = GitHubEvidenceCollector(token="x")
        initial_commit = {"sha": "a" * 40, "commit": {"tree": {"sha": "c" * 40}}}
        tree = {"truncated": False, "tree": []}
        final_commit = {"sha": "b" * 40, "commit": {"tree": {"sha": "d" * 40}}}
        with patch.object(
            collector,
            "_repo",
            return_value={"id": 1, "full_name": "acme/example", "default_branch": "main"},
        ), patch.object(
            collector,
            "_request",
            side_effect=[(initial_commit, {}), (tree, {}), (final_commit, {})],
        ):
            evidence = collector.collect({
                "target": {"kind": "REPOSITORY_SCOPE", "repository": "acme/example", "ref": "main"},
                "review_intent": "review",
            })
        self.assertEqual(evidence["freshness"], "STALE")
        self.assertFalse(evidence["completeness"]["surfaces"]["target_stabilization"])
        self.assertIn(
            "target_selector_moved_during_collection",
            evidence["completeness"]["material_gaps"],
        )


if __name__ == "__main__":
    unittest.main()
