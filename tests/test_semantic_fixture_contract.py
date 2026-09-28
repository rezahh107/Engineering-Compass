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

    def test_owner_context_rubric_tracks_canonical_authority_order(self):
        authority = (ROOT / "docs" / "governance" / "AUTHORITY.md").read_text(encoding="utf-8")
        owner_rule = "1. current explicit owner/project requirements;"
        mandatory_rule = "2. mandatory product/platform/legal/safety constraints;"
        self.assertIn(owner_rule, authority)
        self.assertIn(mandatory_rule, authority)
        self.assertLess(authority.index(owner_rule), authority.index(mandatory_rule))

        rubric = load_fixture("semantic-evaluation-rubric.json")
        criteria = rubric["scenarios"]["EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING"]["criteria"]
        combined = " ".join(criteria).lower()
        self.assertNotIn("higher-order", combined)
        self.assertNotIn("override owner", combined)

        authority_criterion = next(
            (criterion for criterion in criteria if "canonical authority/evidence boundary" in criterion.lower()),
            None,
        )
        self.assertIsNotNone(authority_criterion)
        normalized = authority_criterion.lower()
        self.assertIn("owner acceptance may rebut an engineering presumption", normalized)
        self.assertIn("does not manufacture", normalized)

    def test_decision_state_semantics_are_not_severity_mapping(self):
        reasoning = (ROOT / "docs" / "core" / "REASONING_MODEL.md").read_text(encoding="utf-8")
        protocol = (ROOT / "docs" / "governance" / "REVIEW_PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("**GREEN**", reasoning)
        self.assertIn("**YELLOW**", reasoning)
        self.assertIn("**RED**", reasoning)
        self.assertIn("not finding severity levels", reasoning.lower())
        self.assertIn("Do not map severity mechanically to color", protocol)

    def test_root_cause_pipeline_blocks_unqualified_repair_and_preserves_method_lock(self):
        reasoning = (ROOT / "docs" / "core" / "REASONING_MODEL.md").read_text(encoding="utf-8")
        self.assertIn("Finding → Root-Cause Anchor → Root-Cause Qualification", reasoning)
        self.assertIn("do not generate a repair prompt", reasoning)
        self.assertIn("Selected Method Conformance Lock", reasoning)
        self.assertIn("SELECTED_METHOD_INFEASIBLE", reasoning)
        self.assertIn("return to method selection", reasoning)

    def test_freshness_and_partial_evidence_rules_forbid_stale_green(self):
        protocol = (ROOT / "docs" / "governance" / "REVIEW_PROTOCOL.md").read_text(encoding="utf-8")
        verification = (ROOT / "docs" / "governance" / "VERIFICATION.md").read_text(encoding="utf-8")
        rubric = load_fixture("semantic-evaluation-rubric.json")
        ec005 = " ".join(rubric["scenarios"]["EC-EVAL-005_WORKFLOW_UNCERTAIN_OUTCOME"]["criteria"])
        self.assertIn("No stale GREEN", protocol)
        self.assertIn("No stale GREEN", verification)
        self.assertIn("invalidates the previous exact-target GREEN", ec005)
        self.assertIn("Preserves identity-independent provider evidence", ec005)

    def test_evaluator_fidelity_remains_non_canonical(self):
        verification = (ROOT / "docs" / "governance" / "VERIFICATION.md").read_text(encoding="utf-8")
        rubric = load_fixture("semantic-evaluation-rubric.json")
        self.assertIn("non-canonical test artifact", verification)
        self.assertIn("must not introduce a new normative rule", verification)
        self.assertEqual(rubric["authority"], "EVALUATOR_ONLY_NON_CANONICAL")
        self.assertIn("cannot create new Engineering Compass authority", rubric["purpose"])

    def test_control_proportionality_supports_declining_stronger_hardening(self):
        reasoning = (ROOT / "docs" / "core" / "REASONING_MODEL.md").read_text(encoding="utf-8")
        criteria = load_fixture("semantic-evaluation-rubric.json")["scenarios"][
            "EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING"
        ]["criteria"]
        combined = " ".join(criteria)
        self.assertIn("Named-failure first", reasoning)
        self.assertIn("Minimum effective control", reasoning)
        self.assertIn("Blocking is exceptional", reasoning)
        self.assertIn("decline the stronger blocking plan", combined)

    def test_gravity_benchmark_requires_cross_manifestation_synthesis(self):
        gravity = load_fixture("gravity-flow-version-coupling.json")
        criteria = " ".join(
            load_fixture("semantic-evaluation-rubric.json")["scenarios"][gravity["id"]]["criteria"]
        )
        self.assertIn("two prior admission failures occurred on different fingerprinted files", " ".join(gravity["scenario"]["implementation_decisions"]))
        self.assertIn("same failure class", gravity["review_task"])
        self.assertIn("Synthesizes the two independent fingerprint-mismatch manifestations", criteria)
        self.assertIn("defect-class closure", criteria)

    def test_full_route_requires_materially_distinct_methods(self):
        reasoning = (ROOT / "docs" / "core" / "REASONING_MODEL.md").read_text(encoding="utf-8")
        gaps = load_fixture("scenario-driven-gap-discovery.json")
        ec006 = next(row for row in gaps["scenarios"] if row["id"] == "EC-EVAL-006_INTERACTION_FAILURE_AND_BOUNDED_COMBINATORICS")
        criteria = " ".join(
            load_fixture("semantic-evaluation-rubric.json")["scenarios"][ec006["id"]]["criteria"]
        )
        self.assertIn("Otherwise use `FULL`", reasoning)
        self.assertIn("two materially distinct admissible replacement repair families", ec006["review_task"])
        self.assertIn("uses FULL method selection", criteria)
        self.assertIn("does not invent alternatives", criteria)


if __name__ == "__main__":
    unittest.main()
