from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import verify_repo

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(name: str):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


class SemanticFixtureContractTests(unittest.TestCase):
    def test_current_reviewer_fixtures_pass_positive_contract(self):
        gravity = load_fixture("gravity-flow-version-coupling.json")
        controls = load_fixture("control-boundary-semantics.json")
        errors: list[str] = []
        gravity_id = verify_repo.validate_gravity_reviewer_fixture(gravity, errors)
        control_ids = verify_repo.validate_control_reviewer_fixture(controls, errors)
        self.assertEqual(errors, [])
        self.assertEqual(gravity_id, "EC-EVAL-001_GRAVITY_FLOW_VERSION_COUPLING")
        self.assertEqual(control_ids, set(verify_repo.CONTROL_INPUT_KEYS))

    def test_gravity_top_level_criteria_is_rejected(self):
        gravity = load_fixture("gravity-flow-version-coupling.json")
        gravity["criteria"] = ["evaluator-only"]
        errors: list[str] = []
        verify_repo.validate_gravity_reviewer_fixture(gravity, errors)
        self.assertTrue(any("unsupported fields" in error and "criteria" in error for error in errors), errors)

    def test_control_row_criteria_is_rejected(self):
        controls = load_fixture("control-boundary-semantics.json")
        controls["scenarios"][0]["criteria"] = ["evaluator-only"]
        errors: list[str] = []
        verify_repo.validate_control_reviewer_fixture(controls, errors)
        self.assertTrue(any("unsupported fields" in error and "criteria" in error for error in errors), errors)

    def test_alternate_evaluator_structure_in_input_is_rejected(self):
        controls = load_fixture("control-boundary-semantics.json")
        controls["scenarios"][0]["input"]["expected_result"] = {"verdict": "PASS"}
        errors: list[str] = []
        verify_repo.validate_control_reviewer_fixture(controls, errors)
        self.assertTrue(any("unsupported fields" in error and "expected_result" in error for error in errors), errors)

    def test_unknown_reviewer_structure_is_fail_closed(self):
        gravity = load_fixture("gravity-flow-version-coupling.json")
        gravity["scenario"]["future_unvalidated_field"] = "would make admission permissive"
        errors: list[str] = []
        verify_repo.validate_gravity_reviewer_fixture(gravity, errors)
        self.assertTrue(any("unsupported fields" in error and "future_unvalidated_field" in error for error in errors), errors)

    def test_evaluator_rubric_criteria_remains_valid_and_ids_match(self):
        gravity = load_fixture("gravity-flow-version-coupling.json")
        controls = load_fixture("control-boundary-semantics.json")
        rubric = load_fixture("semantic-evaluation-rubric.json")
        reviewer_errors: list[str] = []
        scenario_ids = {verify_repo.validate_gravity_reviewer_fixture(gravity, reviewer_errors)}
        scenario_ids.update(verify_repo.validate_control_reviewer_fixture(controls, reviewer_errors))
        self.assertEqual(reviewer_errors, [])
        rubric_errors: list[str] = []
        verify_repo.validate_evaluator_rubric(rubric, scenario_ids, rubric_errors)
        self.assertEqual(rubric_errors, [])
        self.assertTrue(all("criteria" in spec for spec in rubric["scenarios"].values()))
        self.assertEqual(set(rubric["scenarios"]), scenario_ids)


if __name__ == "__main__":
    unittest.main()
