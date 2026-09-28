from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import verify_repo

ROOT = Path(__file__).resolve().parents[2]


class FinalGateSemanticFixtureContractTests(unittest.TestCase):
    def _load(self, name: str):
        return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))

    def _gap_scenario(self, gaps: dict) -> dict:
        return next(
            row for row in gaps["scenarios"] if row["id"] == verify_repo.FINAL_GATE_SCENARIO_ID
        )

    def test_final_gate_scenario_and_evaluator_are_synchronized(self):
        gaps = self._load("scenario-driven-gap-discovery.json")
        rubric = self._load("semantic-evaluation-rubric.json")

        self.assertIsNotNone(self._gap_scenario(gaps))
        self.assertIn(verify_repo.FINAL_GATE_SCENARIO_ID, rubric["scenarios"])
        self.assertTrue(rubric["scenarios"][verify_repo.FINAL_GATE_SCENARIO_ID]["criteria"])

    def test_final_gate_complete_reviewer_payload_excludes_evaluator_only_markers(self):
        gaps = self._load("scenario-driven-gap-discovery.json")
        payload = verify_repo._complete_reviewer_payload_text(gaps, self._gap_scenario(gaps))

        for marker in verify_repo.FINAL_GATE_LEAKAGE_MARKERS:
            self.assertNotIn(marker.lower(), payload)

    def test_final_gate_evaluator_marker_in_reviewer_payload_fails_closed(self):
        gaps = self._load("scenario-driven-gap-discovery.json")
        scenario = self._gap_scenario(gaps)
        marker = verify_repo.FINAL_GATE_LEAKAGE_MARKERS[0]
        scenario["input"]["closure_context"].append(f"Injected evaluator-only answer: {marker}")

        errors: list[str] = []
        verify_repo.validate_gap_reviewer_fixture(gaps, errors)

        self.assertTrue(
            any(
                "complete reviewer-visible payload leaks evaluator-only answer marker" in error
                and marker in error
                for error in errors
            ),
            errors,
        )

    def test_final_gate_canonical_markers_compose_with_existing_reasoning_base(self):
        errors: list[str] = []
        verify_repo.check_final_gate_strict_contract(errors)
        self.assertEqual(errors, [])

    def test_existing_ec_eval_001_through_010_ids_remain_present(self):
        gravity = self._load("gravity-flow-version-coupling.json")
        controls = self._load("control-boundary-semantics.json")
        gaps = self._load("scenario-driven-gap-discovery.json")

        scenario_ids = {gravity["id"]}
        scenario_ids.update(row["id"] for row in controls["scenarios"])
        scenario_ids.update(row["id"] for row in gaps["scenarios"])

        expected_existing = {
            "EC-EVAL-001_GRAVITY_FLOW_VERSION_COUPLING",
            "EC-EVAL-002_REPOSITORY_CODE_IS_NOT_EXECUTION",
            "EC-EVAL-003_MODEL_MEDIATED_IS_NOT_FORCED_PATH",
            "EC-EVAL-004_VALIDATOR_PASS_IS_NOT_SEMANTIC_PROOF",
            "EC-EVAL-005_WORKFLOW_UNCERTAIN_OUTCOME",
            "EC-EVAL-006_INTERACTION_FAILURE_AND_BOUNDED_COMBINATORICS",
            "EC-EVAL-007_DRIFT_MODEL_COMPLETENESS_AND_STOP",
            "EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING",
            "EC-EVAL-009_PACKAGE_REVISION_STALENESS",
            "EC-EVAL-010_REVIEW_TO_HANDOFF_FIDELITY",
        }

        self.assertTrue(expected_existing.issubset(scenario_ids))


if __name__ == "__main__":
    unittest.main()
