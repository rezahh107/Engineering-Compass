from __future__ import annotations

import json
import unittest
from pathlib import Path

from engineering_compass.model import ContractError, validate_request
from engineering_compass.projection import _project_action_current as project_action
from engineering_compass.prompt_pipeline import _build_prompt_pipeline_intake_current as build_prompt_pipeline_intake, load_lock
from engineering_compass.root_cause import validate_assessment

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(name: str):
    return json.loads((ROOT / "fixtures" / "runtime" / name).read_text(encoding="utf-8"))


class RuntimeTests(unittest.TestCase):
    def test_review_request_separates_caller_intent_from_facts(self):
        request = {
            "target": {"kind": "PR_SCOPE", "repository": "acme/example", "pr_number": 5},
            "review_intent": "Deep engineering review",
            "inspection_profile": "deep",
        }
        validate_request(request)
        request["head_sha"] = "a" * 40
        with self.assertRaises(ContractError):
            validate_request(request)

    def test_full_root_cause_repair_projects_implementation(self):
        fixture = load_fixture("repair-full.json")
        validation = validate_assessment(fixture["evidence"], fixture["assessment"])
        self.assertEqual(validation["routes"]["RC-1"], "FULL")
        self.assertEqual(validation["authorized_repair_group_ids"], ["RC-1"])
        projection = project_action(fixture["evidence"], fixture["assessment"])
        self.assertEqual(projection["action"], "IMPLEMENT_REPAIR")
        self.assertTrue(projection["may_modify_code"])
        self.assertEqual(projection["recipient"], "implementer_model")

    def test_confirmed_finding_without_confirmed_root_cause_cannot_patch(self):
        fixture = load_fixture("root-cause-unproven.json")
        projection = project_action(fixture["evidence"], fixture["assessment"])
        self.assertEqual(projection["action"], "VERIFY_ROOT_CAUSE")
        self.assertFalse(projection["may_modify_code"])

    def test_prompt_pipeline_handoff_binds_root_cause_method_lock_and_tests(self):
        fixture = load_fixture("repair-full.json")
        intake = build_prompt_pipeline_intake(fixture["evidence"], fixture["assessment"])
        self.assertEqual(intake["domain_hint"], "prompt_generation")
        self.assertIn("Confirmed root cause", intake["request"])
        self.assertIn("Conformance lock", intake["request"])
        self.assertIn("Falsification obligations", intake["request"])
        self.assertIn("[IMPLEMENTATION CONTRACT]", intake["request"])
        self.assertIn("SELECTED_METHOD_INFEASIBLE", intake["request"])
        self.assertTrue(intake["potential_downstream_execution"])

    def test_no_direct_prompt_when_action_does_not_require_one(self):
        fixture = load_fixture("repair-full.json")
        assessment = json.loads(json.dumps(fixture["assessment"]))
        assessment["findings"] = []
        assessment["root_cause_groups"] = []
        assessment["method_coverage"] = []
        projection = project_action(fixture["evidence"], assessment)
        self.assertEqual(projection["action"], "STOP_AT_SUFFICIENCY")
        with self.assertRaises(ContractError):
            build_prompt_pipeline_intake(fixture["evidence"], assessment)

    def test_equivalent_finalists_route_owner_decision(self):
        fixture = load_fixture("repair-full.json")
        assessment = json.loads(json.dumps(fixture["assessment"]))
        group = assessment["root_cause_groups"][0]
        group["selection"] = {
            "state": "EQUIVALENT_FINALISTS",
            "selected_method_id": None,
            "rationale": "Evidence does not distinguish remaining admissible methods.",
        }
        group["conformance_lock"] = None
        group["falsification_obligations"] = []
        projection = project_action(fixture["evidence"], assessment)
        self.assertEqual(projection["action"], "OWNER_DECISION_REQUIRED")
        self.assertFalse(projection["prompt_required"])

    def test_duplicate_method_signature_is_rejected(self):
        fixture = load_fixture("repair-full.json")
        assessment = json.loads(json.dumps(fixture["assessment"]))
        methods = assessment["root_cause_groups"][0]["methods"]
        methods[1]["decision_properties"] = dict(methods[0]["decision_properties"])
        with self.assertRaises(ContractError):
            validate_assessment(fixture["evidence"], assessment)

    def test_prompt_pipeline_lock_matches_inspected_identity(self):
        lock = load_lock()
        self.assertEqual(lock["source_repository"], "rezahh107/Prompt-Pipeline")
        self.assertEqual(lock["source_commit_sha"], "488499d9008b325264159f6c7fc5dbffe4a9e7b2")
        self.assertEqual(lock["domain"], "prompt_generation")
        self.assertEqual(lock["domain_version"], "2026.3")
        self.assertEqual(lock["contract_version"], "1.1")

    def test_numeric_scoring_is_rejected(self):
        fixture = load_fixture("repair-full.json")
        assessment = json.loads(json.dumps(fixture["assessment"]))
        assessment["root_cause_groups"][0]["methods"][0]["comparison"][0]["score"] = 10
        with self.assertRaises(ContractError):
            validate_assessment(fixture["evidence"], assessment)


if __name__ == "__main__":
    unittest.main()
