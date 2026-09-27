from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engineering_compass.model import ContractError, finalize_evidence_bundle
from engineering_compass.projection import project_action
from engineering_compass.prompt_pipeline import build_prompt_pipeline_intake, verify_prompt_pipeline_checkout
from engineering_compass.root_cause import validate_assessment

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(name: str):
    return json.loads((ROOT / "fixtures" / "runtime" / name).read_text(encoding="utf-8"))


def clone(value):
    return copy.deepcopy(value)


def run(cwd: Path, *args: str) -> str:
    completed = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True)
    return completed.stdout.strip()


class RepairInvariantTests(unittest.TestCase):
    def test_selected_method_lock_mismatches_fail_closed(self):
        fixture = load_fixture("repair-full.json")
        for key in ("enforcement_boundary", "authority_owner", "failure_semantics"):
            with self.subTest(key=key):
                assessment = clone(fixture["assessment"])
                assessment["root_cause_groups"][0]["conformance_lock"]["locked_properties"][key] = "contradiction"
                with self.assertRaises(ContractError):
                    project_action(fixture["evidence"], assessment)

    def test_anchor_lock_boundary_mismatch_fails_closed(self):
        fixture = load_fixture("repair-full.json")
        assessment = clone(fixture["assessment"])
        assessment["root_cause_groups"][0]["anchor"]["correct_enforcement_boundary"] = "different boundary"
        with self.assertRaises(ContractError):
            validate_assessment(fixture["evidence"], assessment)

    def test_full_empty_comparison_cannot_implement(self):
        fixture = load_fixture("repair-full.json")
        assessment = clone(fixture["assessment"])
        for method in assessment["root_cause_groups"][0]["methods"]:
            method["comparison"] = []
        projection = project_action(fixture["evidence"], assessment)
        self.assertEqual(projection["action"], "COLLECT_EVIDENCE")
        self.assertFalse(projection["may_modify_code"])

    def test_full_partial_comparison_cannot_implement(self):
        fixture = load_fixture("repair-full.json")
        assessment = clone(fixture["assessment"])
        group = assessment["root_cause_groups"][0]
        group["methods"][1]["comparison"] = group["methods"][1]["comparison"][:2]
        projection = project_action(fixture["evidence"], assessment)
        self.assertEqual(projection["action"], "COLLECT_EVIDENCE")
        self.assertFalse(projection["may_modify_code"])

    def test_all_optional_falsification_cannot_implement(self):
        fixture = load_fixture("repair-full.json")
        assessment = clone(fixture["assessment"])
        for obligation in assessment["root_cause_groups"][0]["falsification_obligations"]:
            obligation["required"] = False
        projection = project_action(fixture["evidence"], assessment)
        self.assertEqual(projection["action"], "COMPLETE_REPAIR_DESIGN")
        self.assertFalse(projection["may_modify_code"])

    def test_repair_finding_must_be_member_of_referenced_group(self):
        fixture = load_fixture("repair-full.json")
        assessment = clone(fixture["assessment"])
        unrelated = clone(assessment["findings"][0])
        unrelated.update({"finding_id": "UNRELATED", "repair_disposition": "NONE", "root_cause_group_id": None})
        assessment["findings"].append(unrelated)
        assessment["root_cause_groups"][0]["finding_ids"] = ["UNRELATED"]
        with self.assertRaises(ContractError):
            validate_assessment(fixture["evidence"], assessment)

    def test_selected_nonrepair_group_is_not_serialized(self):
        fixture = load_fixture("repair-full.json")
        assessment = clone(fixture["assessment"])
        extra_finding = clone(assessment["findings"][0])
        extra_finding.update({"finding_id": "EC-FND-NONE", "repair_disposition": "NONE", "root_cause_group_id": None})
        assessment["findings"].append(extra_finding)
        extra_group = clone(assessment["root_cause_groups"][0])
        extra_group["group_id"] = "RC-NONE"
        extra_group["finding_ids"] = ["EC-FND-NONE"]
        assessment["root_cause_groups"].append(extra_group)

        validation = validate_assessment(fixture["evidence"], assessment)
        self.assertEqual(validation["authorized_repair_group_ids"], ["RC-1"])
        intake = build_prompt_pipeline_intake(fixture["evidence"], assessment)
        self.assertIn("Root-cause group: RC-1", intake["request"])
        self.assertNotIn("RC-NONE", intake["request"])

    def test_projection_precedence_is_global_and_order_invariant(self):
        fixture = load_fixture("repair-full.json")
        assessment = clone(fixture["assessment"])
        first = assessment["root_cause_groups"][0]
        second = clone(first)
        second_finding = clone(assessment["findings"][0])
        second_finding.update({"finding_id": "EC-FND-002", "root_cause_group_id": "RC-2"})
        assessment["findings"].append(second_finding)
        second["group_id"] = "RC-2"
        second["finding_ids"] = ["EC-FND-002"]
        second["selection"] = {
            "state": "INSUFFICIENT_EVIDENCE",
            "selected_method_id": None,
            "rationale": "Comparison evidence is incomplete.",
        }
        second["conformance_lock"] = None
        second["falsification_obligations"] = []
        assessment["root_cause_groups"].append(second)

        first["anchor"]["state"] = "NOT_PROVEN"
        first["anchor"]["confirmed_root_cause"] = "unknown"
        first["anchor"]["correct_enforcement_boundary"] = "unknown"
        first["anchor"]["explicit_unknowns"] = ["causal mechanism", "boundary"]

        action_before = project_action(fixture["evidence"], assessment)["action"]
        assessment["findings"].reverse()
        assessment["root_cause_groups"].reverse()
        action_after = project_action(fixture["evidence"], assessment)["action"]
        self.assertEqual(action_before, "VERIFY_ROOT_CAUSE")
        self.assertEqual(action_after, action_before)

    def test_same_head_materially_changed_snapshot_rejects_old_assessment(self):
        fixture = load_fixture("repair-full.json")
        evidence_b = clone(fixture["evidence"])
        evidence_b["target"]["pr_number"] = 43
        evidence_b["identity"]["base_sha"] = "e" * 40
        evidence_b["evidence_records"][0]["payload"] = "different evidence at the same head and IDs"
        finalize_evidence_bundle(evidence_b)
        self.assertNotEqual(evidence_b["evidence_digest"], fixture["evidence"]["evidence_digest"])
        with self.assertRaises(ContractError):
            validate_assessment(evidence_b, fixture["assessment"])

    def test_legacy_snapshot_contract_fails_closed(self):
        fixture = load_fixture("repair-full.json")
        evidence = clone(fixture["evidence"])
        evidence["schema_version"] = 1
        with self.assertRaisesRegex(ContractError, "schema_version must be 2"):
            validate_assessment(evidence, fixture["assessment"])

    def _fake_prompt_checkout(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name) / "prompt"
        root.mkdir()
        run(root, "git", "init", "-q")
        run(root, "git", "config", "user.email", "test@example.com")
        run(root, "git", "config", "user.name", "Test")
        (root / "scripts").mkdir()
        (root / "scripts" / "peac-generate.ts").write_text("export const x = 1;\n", encoding="utf-8")
        (root / "package.json").write_text('{"scripts":{"peac:generate":"tsx scripts/peac-generate.ts"}}\n', encoding="utf-8")
        (root / ".gitignore").write_text(
            "node_modules/\n.pnpm-store/\noutputs/\ndist/\ncoverage/\n.env\n*.tsbuildinfo\n",
            encoding="utf-8",
        )
        run(root, "git", "add", ".")
        run(root, "git", "commit", "-qm", "fixture")
        head = run(root, "git", "rev-parse", "HEAD")
        blob = run(root, "git", "rev-parse", "HEAD:scripts/peac-generate.ts")
        lock_path = Path(temp.name) / "lock.json"
        lock_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "source_repository": "fixture/prompt",
                    "source_commit_sha": head,
                    "domain": "prompt_generation",
                    "domain_version": "test",
                    "governing_files": [{"path": "scripts/peac-generate.ts", "blob_sha": blob}],
                }
            ),
            encoding="utf-8",
        )
        return temp, root, lock_path

    def test_dirty_tracked_governing_prompt_file_fails_before_execution(self):
        temp, root, lock_path = self._fake_prompt_checkout()
        try:
            (root / "scripts" / "peac-generate.ts").write_text("export const x = 2;\n", encoding="utf-8")
            with patch("engineering_compass.prompt_pipeline.LOCK_PATH", lock_path), self.assertRaises(ContractError):
                verify_prompt_pipeline_checkout(root)
        finally:
            temp.cleanup()

    def test_dirty_other_tracked_execution_file_fails_before_execution(self):
        temp, root, lock_path = self._fake_prompt_checkout()
        try:
            (root / "package.json").write_text('{"scripts":{"peac:generate":"node unexpected.js"}}\n', encoding="utf-8")
            with patch("engineering_compass.prompt_pipeline.LOCK_PATH", lock_path), self.assertRaises(ContractError):
                verify_prompt_pipeline_checkout(root)
        finally:
            temp.cleanup()

    def test_generated_install_output_allowed_but_ignored_env_is_not(self):
        temp, root, lock_path = self._fake_prompt_checkout()
        try:
            (root / "node_modules" / "pkg").mkdir(parents=True)
            (root / "node_modules" / "pkg" / "index.js").write_text("generated\n", encoding="utf-8")
            with patch("engineering_compass.prompt_pipeline.LOCK_PATH", lock_path):
                result = verify_prompt_pipeline_checkout(root)
            self.assertEqual(result["executable_worktree"], "SOURCE_CLEAN")

            (root / ".env").write_text("MUTATES_RUNTIME=1\n", encoding="utf-8")
            with patch("engineering_compass.prompt_pipeline.LOCK_PATH", lock_path), self.assertRaises(ContractError):
                verify_prompt_pipeline_checkout(root)
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
