from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import verify_repo

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(name: str):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def semantic_errors(gravity=None, controls=None, gaps=None, rubric=None) -> list[str]:
    fixtures = {
        verify_repo.SCENARIO_FIXTURES[0]: gravity if gravity is not None else load_fixture("gravity-flow-version-coupling.json"),
        verify_repo.SCENARIO_FIXTURES[1]: controls if controls is not None else load_fixture("control-boundary-semantics.json"),
        verify_repo.SCENARIO_FIXTURES[2]: gaps if gaps is not None else load_fixture("scenario-driven-gap-discovery.json"),
        verify_repo.EVALUATOR_RUBRIC: rubric if rubric is not None else load_fixture("semantic-evaluation-rubric.json"),
    }

    def fake_load_json(rel: str, _errors: list[str]):
        return copy.deepcopy(fixtures[rel])

    errors: list[str] = []
    with patch.object(verify_repo, "load_json", side_effect=fake_load_json):
        verify_repo.check_semantic_evaluation_fixtures(errors)
    return errors


class SemanticFixtureContractTests(unittest.TestCase):
    def test_current_reviewer_fixtures_and_evaluator_rubric_pass(self):
        rubric = load_fixture("semantic-evaluation-rubric.json")
        self.assertEqual(semantic_errors(), [])
        self.assertTrue(all("criteria" in spec for spec in rubric["scenarios"].values()))

    def test_gravity_top_level_criteria_makes_verifier_fail(self):
        gravity = load_fixture("gravity-flow-version-coupling.json")
        gravity["criteria"] = ["evaluator-only"]
        errors = semantic_errors(gravity=gravity)
        self.assertTrue(any("unsupported fields" in error and "criteria" in error for error in errors), errors)

    def test_control_row_criteria_makes_verifier_fail(self):
        controls = load_fixture("control-boundary-semantics.json")
        controls["scenarios"][0]["criteria"] = ["evaluator-only"]
        errors = semantic_errors(controls=controls)
        self.assertTrue(any("unsupported fields" in error and "criteria" in error for error in errors), errors)

    def test_alternate_evaluator_structure_in_input_makes_verifier_fail(self):
        controls = load_fixture("control-boundary-semantics.json")
        controls["scenarios"][0]["input"]["expected_result"] = {"verdict": "PASS"}
        errors = semantic_errors(controls=controls)
        self.assertTrue(any("unsupported fields" in error and "expected_result" in error for error in errors), errors)

    def test_unknown_reviewer_structure_is_fail_closed(self):
        gravity = load_fixture("gravity-flow-version-coupling.json")
        gravity["scenario"]["future_unvalidated_field"] = "would make admission permissive"
        errors = semantic_errors(gravity=gravity)
        self.assertTrue(any("unsupported fields" in error and "future_unvalidated_field" in error for error in errors), errors)

    def test_gap_row_criteria_makes_verifier_fail(self):
        gaps = load_fixture("scenario-driven-gap-discovery.json")
        gaps["scenarios"][0]["criteria"] = ["evaluator-only"]
        errors = semantic_errors(gaps=gaps)
        self.assertTrue(any("unsupported fields" in error and "criteria" in error for error in errors), errors)

    def test_gap_input_unknown_structure_makes_verifier_fail(self):
        gaps = load_fixture("scenario-driven-gap-discovery.json")
        gaps["scenarios"][1]["input"]["expected_result"] = {"verdict": "PASS"}
        errors = semantic_errors(gaps=gaps)
        self.assertTrue(any("unsupported fields" in error and "expected_result" in error for error in errors), errors)

    def test_scenario_and_rubric_id_parity_still_fails_closed(self):
        rubric = load_fixture("semantic-evaluation-rubric.json")
        rubric["scenarios"].pop("EC-EVAL-007_DRIFT_MODEL_COMPLETENESS_AND_STOP")
        errors = semantic_errors(rubric=rubric)
        self.assertTrue(any("semantic scenario/rubric ids differ" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
