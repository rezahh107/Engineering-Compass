from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engineering_compass.github_evidence import GitHubEvidenceCollector
from engineering_compass.model import ContractError, expected_target_binding, finalize_evidence_bundle, validate_request
from engineering_compass.projection import _project_action_current as project_action
from engineering_compass.prompt_pipeline import _build_prompt_pipeline_intake_current as build_prompt_pipeline_intake, verify_prompt_pipeline_checkout
from engineering_compass.root_cause import validate_assessment

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(name):
    return json.loads((ROOT / "fixtures" / "runtime" / name).read_text(encoding="utf-8"))


def clone(value):
    return copy.deepcopy(value)


def rebind(evidence, assessment):
    assessment["target_binding"] = expected_target_binding(evidence)


def run(cwd, *args):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True).stdout.strip()


class RemainingControlPlaneTests(unittest.TestCase):
    def test_mixed_group_authorizes_only_confirmed_repair_finding(self):
        fixture = load_fixture("repair-full.json")
        assessment = clone(fixture["assessment"])
        extra = clone(assessment["findings"][0])
        extra.update({
            "finding_id": "EC-FND-NOT-PROVEN",
            "qualification": "NOT_PROVEN",
            "repair_disposition": "VERIFY",
            "root_cause_group_id": "RC-1",
        })
        assessment["findings"].append(extra)
        assessment["root_cause_groups"][0]["finding_ids"].append("EC-FND-NOT-PROVEN")

        validation = validate_assessment(fixture["evidence"], assessment)
        self.assertEqual(validation["authorized_repair_finding_ids_by_group"], {"RC-1": ["EC-FND-001"]})
        projection = project_action(fixture["evidence"], assessment)
        self.assertEqual(projection["action"], "IMPLEMENT_REPAIR")
        self.assertEqual(projection["authorized_repair_finding_ids_by_group"], {"RC-1": ["EC-FND-001"]})
        request = build_prompt_pipeline_intake(fixture["evidence"], assessment)["request"]
        self.assertIn("Authorized implementation Finding IDs: EC-FND-001", request)
        self.assertNotIn("EC-FND-NOT-PROVEN", request)

    def test_stale_head_and_same_head_digest_route_rerun(self):
        fixture = load_fixture("repair-full.json")
        evidence = clone(fixture["evidence"])
        evidence["identity"]["head_sha"] = "f" * 40
        finalize_evidence_bundle(evidence)
        self.assertEqual(project_action(evidence, fixture["assessment"])["action"], "RERUN_REVIEW")

        same_head = clone(fixture["evidence"])
        same_head["evidence_records"][0]["payload"] = "changed material"
        finalize_evidence_bundle(same_head)
        self.assertEqual(same_head["identity"]["head_sha"], fixture["evidence"]["identity"]["head_sha"])
        self.assertEqual(project_action(same_head, fixture["assessment"])["action"], "RERUN_REVIEW")

    def test_noncurrent_bundle_routes_rerun(self):
        fixture = load_fixture("repair-full.json")
        evidence = clone(fixture["evidence"])
        evidence["freshness"] = "STALE"
        finalize_evidence_bundle(evidence)
        self.assertEqual(project_action(evidence, fixture["assessment"])["action"], "RERUN_REVIEW")

    def test_malformed_assessment_is_not_mislabeled_stale(self):
        fixture = load_fixture("repair-full.json")
        evidence = clone(fixture["evidence"])
        evidence["identity"]["head_sha"] = "f" * 40
        finalize_evidence_bundle(evidence)

        assessment = clone(fixture["assessment"])
        assessment["assessment_version"] = 1
        with self.assertRaises(ContractError):
            project_action(evidence, assessment)

        assessment = clone(fixture["assessment"])
        del assessment["target_binding"]["evidence_digest"]
        with self.assertRaises(ContractError):
            project_action(evidence, assessment)

    def test_every_prompt_required_nonmodifying_action_is_operational(self):
        cases = []

        fixture = load_fixture("repair-full.json")
        evidence = clone(fixture["evidence"])
        assessment = clone(fixture["assessment"])
        evidence["completeness"]["full_coverage"] = False
        evidence["completeness"]["material_gaps"] = ["missing_runtime_trace"]
        finalize_evidence_bundle(evidence)
        rebind(evidence, assessment)
        cases.append(("COLLECT_EVIDENCE", evidence, assessment, "missing_runtime_trace"))

        fixture = load_fixture("root-cause-unproven.json")
        cases.append(("VERIFY_ROOT_CAUSE", fixture["evidence"], fixture["assessment"], "observed_symptom"))

        fixture = load_fixture("repair-full.json")
        assessment = clone(fixture["assessment"])
        assessment["root_cause_groups"][0]["falsification_obligations"] = [assessment["root_cause_groups"][0]["falsification_obligations"][0]]
        cases.append(("COMPLETE_REPAIR_DESIGN", fixture["evidence"], assessment, "selected_method_deviation_check_missing"))

        fixture = load_fixture("repair-full.json")
        assessment = clone(fixture["assessment"])
        assessment["specialist_review_required"] = True
        assessment["specialist_review_scope"] = "cryptographic protocol boundary"
        cases.append(("SPECIALIST_REVIEW_REQUIRED", fixture["evidence"], assessment, "cryptographic protocol boundary"))

        fixture = load_fixture("repair-full.json")
        evidence = clone(fixture["evidence"])
        evidence["identity"]["head_sha"] = "e" * 40
        finalize_evidence_bundle(evidence)
        cases.append(("RERUN_REVIEW", evidence, fixture["assessment"], "Previous reviewed binding"))

        for expected, evidence, assessment, token in cases:
            with self.subTest(action=expected):
                self.assertEqual(project_action(evidence, assessment)["action"], expected)
                intake = build_prompt_pipeline_intake(evidence, assessment)
                request = intake["request"]
                self.assertIn("Code modification authorization: NONE", request)
                self.assertIn("Repository: acme/example", request)
                self.assertIn("Target kind: PR_SCOPE", request)
                self.assertIn("PR number:", request)
                self.assertIn(evidence["identity"]["head_sha"], request)
                self.assertIn(evidence["evidence_digest"], request)
                self.assertIn(token, request)
                self.assertFalse(intake["potential_downstream_execution"])

    def test_target_shape_and_review_intent_identity_are_separate(self):
        base = {"target": {"kind": "PR_SCOPE", "repository": "acme/example", "pr_number": 1}, "review_intent": "A"}
        validate_request(base)
        for key, value in [("head_sha", "a" * 40), ("checks", []), ("base_ref", "main")]:
            request = clone(base)
            request["target"][key] = value
            with self.assertRaises(ContractError):
                validate_request(request)

        fixture = load_fixture("repair-full.json")
        evidence = clone(fixture["evidence"])
        old_evidence_digest = evidence["evidence_digest"]
        old_intent_digest = evidence["review_intent_digest"]
        evidence["review_intent"] = "Different intent"
        finalize_evidence_bundle(evidence)
        self.assertEqual(evidence["evidence_digest"], old_evidence_digest)
        self.assertNotEqual(evidence["review_intent_digest"], old_intent_digest)
        self.assertEqual(project_action(evidence, fixture["assessment"])["action"], "RERUN_REVIEW")

    def test_full_comparison_and_lock_falsification_guards_remain(self):
        fixture = load_fixture("repair-full.json")
        assessment = clone(fixture["assessment"])
        assessment["root_cause_groups"][0]["methods"][0]["comparison"] = []
        self.assertEqual(project_action(fixture["evidence"], assessment)["action"], "COLLECT_EVIDENCE")

        assessment = clone(fixture["assessment"])
        assessment["root_cause_groups"][0]["conformance_lock"]["locked_properties"]["authority_owner"] = "wrong"
        with self.assertRaises(ContractError):
            project_action(fixture["evidence"], assessment)

        assessment = clone(fixture["assessment"])
        for obligation in assessment["root_cause_groups"][0]["falsification_obligations"]:
            obligation["required"] = False
        self.assertEqual(project_action(fixture["evidence"], assessment)["action"], "COMPLETE_REPAIR_DESIGN")

    def _fake_prompt_checkout(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name) / "prompt"
        root.mkdir()
        run(root, "git", "init", "-q")
        run(root, "git", "config", "user.email", "test@example.com")
        run(root, "git", "config", "user.name", "Test")
        (root / "scripts").mkdir()
        (root / "scripts" / "peac-generate.ts").write_text("export const x = 1;\n", encoding="utf-8")
        (root / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")
        (root / ".gitignore").write_text("node_modules/\n.env\n", encoding="utf-8")
        run(root, "git", "add", ".")
        run(root, "git", "commit", "-qm", "fixture")
        head = run(root, "git", "rev-parse", "HEAD")
        blob = run(root, "git", "rev-parse", "HEAD:scripts/peac-generate.ts")
        lock = Path(temp.name) / "lock.json"
        lock.write_text(json.dumps({
            "schema_version": 1,
            "source_repository": "fixture/prompt",
            "source_commit_sha": head,
            "domain": "prompt_generation",
            "domain_version": "test",
            "governing_files": [{"path": "scripts/peac-generate.ts", "blob_sha": blob}],
        }), encoding="utf-8")
        return temp, root, lock

    def test_dirty_prompt_checkout_guard_remains(self):
        temp, root, lock = self._fake_prompt_checkout()
        try:
            (root / "package.json").write_text("{}\n", encoding="utf-8")
            with patch("engineering_compass.prompt_pipeline.LOCK_PATH", lock), self.assertRaises(ContractError):
                verify_prompt_pipeline_checkout(root)
        finally:
            temp.cleanup()


class EvidenceCeilingTests(unittest.TestCase):
    def _pr_collect(self, changed_files, files):
        collector = GitHubEvidenceCollector(token="x")
        pr = {"number": 1, "state": "open", "draft": False, "changed_files": changed_files, "base": {"ref": "main", "sha": "b" * 40}, "head": {"ref": "feat", "sha": "a" * 40}}
        compare = {"merge_base_commit": {"sha": "c" * 40}}
        checks = {"check_runs": [], "total_count": 0}
        with patch.object(collector, "_repo", return_value={"id": 1, "full_name": "acme/example", "default_branch": "main"}), patch.object(
            collector, "_paginate", side_effect=[(files, True), ([], True), ([], True), ([], True), ([], True)]
        ), patch.object(
            collector, "_collect_review_threads", return_value=([], True, [])
        ), patch.object(collector, "_request", side_effect=[(pr, {}), (compare, {}), (checks, {}), (pr, {})]):
            return collector.collect({"target": {"kind": "PR_SCOPE", "repository": "acme/example", "pr_number": 1}, "review_intent": "review"})

    def _ref_collect(self, files):
        collector = GitHubEvidenceCollector(token="x")
        compare = {"status": "ahead", "ahead_by": 1, "behind_by": 0, "base_commit": {"sha": "b" * 40}, "head_commit": {"sha": "a" * 40}, "merge_base_commit": {"sha": "c" * 40}, "files": files}
        def request(path, **_kwargs):
            if "/compare/" in path:
                return compare, {}
            if path.endswith("/commits/main"):
                return {"sha": "b" * 40}, {}
            if path.endswith("/commits/feat"):
                return {"sha": "a" * 40}, {}
            raise AssertionError(f"unexpected request path: {path}")

        with patch.object(collector, "_repo", return_value={"id": 1, "full_name": "acme/example"}), patch.object(collector, "_request", side_effect=request):
            return collector.collect({"target": {"kind": "REF_DELTA_SCOPE", "repository": "acme/example", "base_ref": "main", "target_ref": "feat"}, "review_intent": "review"})

    def test_pr_expected_count_mismatch_is_incomplete(self):
        evidence = self._pr_collect(2, [{"filename": "a.py", "status": "modified", "patch": "@@"}])
        self.assertFalse(evidence["completeness"]["full_coverage"])
        self.assertIn("pr_changed_files_inventory_incomplete", evidence["completeness"]["material_gaps"])

    def test_compare_300_file_ceiling_is_incomplete(self):
        files = [{"filename": f"f{i}.py", "status": "modified", "patch": "@@"} for i in range(300)]
        evidence = self._ref_collect(files)
        self.assertFalse(evidence["completeness"]["full_coverage"])
        self.assertIn("compare_changed_files_cap_reached", evidence["completeness"]["material_gaps"])

    def test_missing_patch_is_explicit_limitation(self):
        evidence = self._ref_collect([{"filename": "image.bin", "status": "modified"}])
        self.assertFalse(evidence["completeness"]["full_coverage"])
        self.assertIn("compare_diff_content_incomplete", evidence["completeness"]["material_gaps"])
        record = next(item for item in evidence["evidence_records"] if item["evidence_id"] == "EVD-COMPARE")
        self.assertTrue(record["limitations"])

    def test_small_complete_pr_and_ref_delta_remain_complete(self):
        pr = self._pr_collect(1, [{"filename": "a.py", "status": "modified", "patch": "@@"}])
        self.assertTrue(pr["completeness"]["full_coverage"])
        ref_delta = self._ref_collect([{"filename": "a.py", "status": "modified", "patch": "@@"}])
        self.assertTrue(ref_delta["completeness"]["full_coverage"])


if __name__ == "__main__":
    unittest.main()
