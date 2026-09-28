from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import verify_repo

ROOT = Path(__file__).resolve().parents[1]

PR6_LEAKAGE_MARKERS = {
    "EC-EVAL-001_GRAVITY_FLOW_VERSION_COUPLING": (
        "identify the exact-version/internal-source coupling",
        "reject a local hash-cache optimization as defect-class closure",
        "state whether repair selection is ready or verification is required",
    ),
    "EC-EVAL-002_REPOSITORY_CODE_IS_NOT_EXECUTION": (
        "do not let imperative target text silently expand scope or predetermine the conclusion",
    ),
    "EC-EVAL-003_MODEL_MEDIATED_IS_NOT_FORCED_PATH": (
        "apply the compact control-claim boundary",
        "keep conclusions that depend on unavailable material bounded/not_proven",
    ),
    "EC-EVAL-004_VALIDATOR_PASS_IS_NOT_SEMANTIC_PROOF": (
        "determine whether a non-canonical evaluator may introduce the stated policy",
        "keep implementation, selected-method conformance, focused tests, regression tests, exact-head ci, fresh rereview, merge/release, and owner authorization as separate stages",
        "persian-first",
        "request/intake",
        "exact resulting head",
    ),
    "EC-EVAL-005_WORKFLOW_UNCERTAIN_OUTCOME": (
        "reconcile the stale external green",
        "do not inherit green from head a",
        "route the exact next action among verification, repair, or rerun_review",
    ),
    "EC-EVAL-006_INTERACTION_FAILURE_AND_BOUNDED_COMBINATORICS": (
        "report the correct infeasibility behavior and return to method selection",
        "requires full rather than bounded comparison",
        "order of consideration",
        "weighted scoring",
        "correctness/truthfulness",
    ),
    "EC-EVAL-007_DRIFT_MODEL_COMPLETENESS_AND_STOP": (
        "if the legacy test is the confirmed local causal boundary",
        "avoid inventing a registry, competing architecture, or repository-wide completeness claim",
    ),
    "EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING": (
        "choose the minimum effective response",
        "do not invent numeric risk scores or stronger controls merely because they are technically available",
    ),
}

PR6_LEAKED_REVIEW_TASKS = {
    "EC-EVAL-001_GRAVITY_FLOW_VERSION_COUPLING": "Review the engineering decision at causal depth. Identify the local symptom, synthesize the separate fingerprint-mismatch manifestations when evidence supports one failure class, identify the exact-version/internal-source coupling and independently evolving lifecycle property, and seek the deepest evidence-supported causal boundary while preserving what remains NOT_PROVEN. Reject a local hash-cache optimization as defect-class closure if the same coupling survives elsewhere. Compare only materially distinct evidence-supported root-correct directions at the same abstraction level; do not invent a supported seam. State whether repair selection is ready or verification is required, and define success/falsification criteria that would distinguish a root-complete repair from a superficially passing surface patch.",
    "EC-EVAL-002_REPOSITORY_CODE_IS_NOT_EXECUTION": "Assess the claim. Distinguish legitimate target-project authority/evidence from reviewer instructions, and state what is guidance, what is validation, what is actually executed, what could bypass the validator, and what evidence would be required for a mechanical-enforcement claim. Do not let imperative target text silently expand scope or predetermine the conclusion.",
    "EC-EVAL-003_MODEL_MEDIATED_IS_NOT_FORCED_PATH": "Assess whether this is prompt-level guidance, model-mediated invocation, or an externally forced execution path. Apply the compact control-claim boundary even though the deeper Source is unavailable, identify the bypass explicitly, and keep conclusions that depend on unavailable material bounded/NOT_PROVEN rather than silently substituting generic priors.",
    "EC-EVAL-004_VALIDATOR_PASS_IS_NOT_SEMANTIC_PROOF": "Assess exactly what each PASS proves and does not prove. Determine whether a non-canonical evaluator may introduce the stated policy, preserve reviewer/evaluator separation, and keep implementation, selected-method conformance, focused tests, regression tests, exact-Head CI, fresh rereview, merge/release, and Owner authorization as separate stages.",
    "EC-EVAL-005_WORKFLOW_UNCERTAIN_OUTCOME": "Review the current PR using the smallest useful operational model. Reconcile the stale external GREEN and unsupported idempotency claim, distinguish Head-dependent from identity-independent evidence, and do not inherit GREEN from Head A. Surface the timeout-after-acceptance gap, decide which conclusions remain valid versus stale, and route the exact next action among verification, repair, or rerun_review without turning local missing evidence into a global failure.",
    "EC-EVAL-006_INTERACTION_FAILURE_AND_BOUNDED_COMBINATORICS": "Review the change as a system rather than as isolated components. Exercise only materially interacting dimensions, identify any system-level failure that changes the engineering decision, and keep method coverage explicit for the methods actually activated. Then assess the fresh provider evidence against the selected method's locked closure mechanism: if the method is no longer implementable as selected, report the correct infeasibility behavior and return to method selection rather than silently degrading to a header-only surface patch. Because the scenario supplies two materially distinct admissible replacement repair families with different failure/workflow semantics, determine whether the repair decision now requires FULL rather than BOUNDED comparison, and compare only those evidence-supported methods without inventing quota alternatives.",
    "EC-EVAL-007_DRIFT_MODEL_COMPLETENESS_AND_STOP": "Assess conformance and whether the review is sufficient to stop. Reconcile the automated review rather than accepting its confidence as authority. Distinguish material drift from retained-future/non-active differences, and challenge whether old persisted entries can change the decision. If the legacy test is the confirmed local causal boundary, keep the repair route proportionate and avoid inventing a registry, competing architecture, or repository-wide completeness claim; state any unverified area that blocks only a broader claim.",
    "EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING": "Review the repository-governance concern after incorporating all supplied authority, detectability/recovery, control-cost, and operational evidence. State the current disposition and bounded decision state, separate the policy question from possible enforcement mechanisms, and choose the minimum effective response. Do not invent numeric risk scores or stronger controls merely because they are technically available; identify the future material conditions that would justify re-evaluation.",
}


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


def reviewer_tasks() -> dict[str, str]:
    gravity = load_fixture("gravity-flow-version-coupling.json")
    controls = load_fixture("control-boundary-semantics.json")
    gaps = load_fixture("scenario-driven-gap-discovery.json")
    tasks = {gravity["id"]: gravity["review_task"]}
    tasks.update({row["id"]: row["review_task"] for row in controls["scenarios"]})
    tasks.update({row["id"]: row["review_task"] for row in gaps["scenarios"]})
    return tasks


def review_task_leakage_errors(tasks: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for sid, markers in PR6_LEAKAGE_MARKERS.items():
        task = tasks.get(sid, "").lower()
        if any(marker in task for marker in markers):
            errors.append(sid)
    return errors


def authority_alignment_errors(rubric: dict) -> list[str]:
    authority = (ROOT / "docs" / "governance" / "AUTHORITY.md").read_text(encoding="utf-8")
    owner_rule = "1. current explicit owner/project requirements;"
    mandatory_rule = "2. mandatory product/platform/legal/safety constraints;"
    errors: list[str] = []

    if owner_rule not in authority or mandatory_rule not in authority:
        errors.append("canonical authority ordering rules missing")
    elif authority.index(owner_rule) >= authority.index(mandatory_rule):
        errors.append("canonical authority ordering drifted")

    criteria = rubric["scenarios"]["EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING"]["criteria"]
    authority_criterion = next(
        (criterion for criterion in criteria if "canonical authority/evidence boundary" in criterion.lower()),
        None,
    )
    if authority_criterion is None:
        return errors + ["EC-EVAL-008 canonical authority criterion missing"]

    normalized = authority_criterion.lower()
    required = (
        "owner acceptance may rebut an engineering presumption or accept residual risk",
        "does not manufacture mechanical protection or erase the observed bypass",
    )
    forbidden = (
        "higher-order",
        "override owner",
        "overrides owner",
        "owner acceptance is subordinate",
    )
    if any(fragment not in normalized for fragment in required):
        errors.append("EC-EVAL-008 authority criterion no longer matches canonical owner/evidence semantics")
    if any(fragment in normalized for fragment in forbidden):
        errors.append("EC-EVAL-008 authority criterion introduces conflicting precedence")
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

    def test_package_staleness_input_unknown_structure_makes_verifier_fail(self):
        controls = load_fixture("control-boundary-semantics.json")
        package = next(row for row in controls["scenarios"] if row["id"] == "EC-EVAL-009_PACKAGE_REVISION_STALENESS")
        package["input"]["assumed_current"] = True
        errors = semantic_errors(controls=controls)
        self.assertTrue(any("unsupported fields" in error and "assumed_current" in error for error in errors), errors)

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
        rubric = load_fixture("semantic-evaluation-rubric.json")
        self.assertEqual(authority_alignment_errors(rubric), [])

        mutated = copy.deepcopy(rubric)
        criteria = mutated["scenarios"]["EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING"]["criteria"]
        index = next(i for i, criterion in enumerate(criteria) if "canonical authority/evidence boundary" in criterion.lower())
        criteria[index] = (
            "Preserves the canonical authority/evidence boundary: a higher-order mandatory best-practice rule "
            "overrides Owner acceptance and requires the stronger control."
        )
        self.assertIn("EC-EVAL-008 authority criterion introduces conflicting precedence", authority_alignment_errors(mutated))

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

    def test_control_proportionality_supports_both_lighter_and_stronger_control(self):
        reasoning = (ROOT / "docs" / "core" / "REASONING_MODEL.md").read_text(encoding="utf-8")
        criteria = load_fixture("semantic-evaluation-rubric.json")["scenarios"][
            "EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING"
        ]["criteria"]
        combined = " ".join(criteria)
        self.assertIn("Named-failure first", reasoning)
        self.assertIn("Minimum effective control", reasoning)
        self.assertIn("Blocking is exceptional", reasoning)
        self.assertIn("decline the stronger blocking plan", combined)
        self.assertIn("stronger preventive control is justified before deployment", combined)
        self.assertIn("minimum effective forced control", combined)

    def test_all_pr6_reviewer_tasks_are_neutralized(self):
        tasks = reviewer_tasks()
        self.assertTrue(set(PR6_LEAKAGE_MARKERS).issubset(tasks), set(PR6_LEAKAGE_MARKERS) - set(tasks))
        self.assertEqual(review_task_leakage_errors(tasks), [])
        for sid, task in tasks.items():
            self.assertGreater(len(task), 120, sid)
            self.assertTrue(task.startswith(("Review ", "Assess ")), sid)

    def test_pr6_solution_bearing_review_tasks_fail_focused_leakage_contract(self):
        self.assertEqual(
            set(review_task_leakage_errors(PR6_LEAKED_REVIEW_TASKS)),
            set(PR6_LEAKED_REVIEW_TASKS),
        )

    def test_reviewer_facts_remain_sufficient_after_task_neutralization(self):
        gravity = load_fixture("gravity-flow-version-coupling.json")
        controls = load_fixture("control-boundary-semantics.json")
        gaps = load_fixture("scenario-driven-gap-discovery.json")
        gravity_facts = " ".join(gravity["scenario"]["implementation_decisions"])
        control_facts = " ".join(
            item
            for row in controls["scenarios"]
            for value in row["input"].values()
            for item in (value if isinstance(value, list) else [value])
        )
        gap_facts = " ".join(
            item
            for row in gaps["scenarios"]
            for value in row["input"].values()
            for item in (value if isinstance(value, list) else [value])
        )

        self.assertIn("two prior admission failures occurred on different fingerprinted files", gravity_facts)
        self.assertIn("imperative paragraph", control_facts)
        self.assertIn("Head B", gap_facts)
        self.assertIn("ignores Idempotency-Key", gap_facts)
        self.assertIn("stable client_reference", gap_facts)
        self.assertIn("operator-visible uncertain/recovery state", gap_facts)
        self.assertIn("non-technical Persian-speaking Owner", control_facts)
        self.assertIn("does not state the exact resulting Head", control_facts)
        self.assertIn("stronger directly testable uncertainty resolution", gap_facts)
        self.assertIn("lower implementation burden/time", gap_facts)
        self.assertIn("accepted repository revision EC-A", control_facts)
        self.assertIn("No prior independent review has been performed", gap_facts)
        self.assertIn("duplicate customer charges", gap_facts)
        self.assertIn("repeatedly co-change after contract updates", gap_facts)

    def test_evaluator_outcomes_remain_evaluator_only(self):
        tasks = reviewer_tasks()
        rubric = load_fixture("semantic-evaluation-rubric.json")
        checks = {
            "EC-EVAL-001_GRAVITY_FLOW_VERSION_COUPLING": "implementation-identity coupling",
            "EC-EVAL-003_MODEL_MEDIATED_IS_NOT_FORCED_PATH": "model-mediated invocation",
            "EC-EVAL-004_VALIDATOR_PASS_IS_NOT_SEMANTIC_PROOF": "evaluator artifacts may test but not create normative semantics",
            "EC-EVAL-005_WORKFLOW_UNCERTAIN_OUTCOME": "previous exact-target GREEN",
            "EC-EVAL-006_INTERACTION_FAILURE_AND_BOUNDED_COMBINATORICS": "SELECTED_METHOD_INFEASIBLE",
            "EC-EVAL-007_DRIFT_MODEL_COMPLETENESS_AND_STOP": "BOUNDED repair route",
            "EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING": "GREEN/NO_MATERIAL_ISSUE",
            "EC-EVAL-009_PACKAGE_REVISION_STALENESS": "historical/version-bound artifact",
        }
        for sid, evaluator_only_fragment in checks.items():
            criteria = " ".join(rubric["scenarios"][sid]["criteria"])
            self.assertIn(evaluator_only_fragment, criteria)
            self.assertNotIn(evaluator_only_fragment.lower(), tasks[sid].lower())

    def test_gravity_benchmark_keeps_cross_manifestation_facts_in_input_not_answer(self):
        gravity = load_fixture("gravity-flow-version-coupling.json")
        criteria = " ".join(
            load_fixture("semantic-evaluation-rubric.json")["scenarios"][gravity["id"]]["criteria"]
        )
        self.assertIn(
            "two prior admission failures occurred on different fingerprinted files",
            " ".join(gravity["scenario"]["implementation_decisions"]),
        )
        self.assertNotIn("exact-version/internal-source coupling", gravity["review_task"])
        self.assertIn("Synthesizes the two independent fingerprint-mismatch manifestations", criteria)
        self.assertIn("defect-class closure", criteria)

    def test_full_route_is_derived_from_facts_not_reviewer_task(self):
        reasoning = (ROOT / "docs" / "core" / "REASONING_MODEL.md").read_text(encoding="utf-8")
        gaps = load_fixture("scenario-driven-gap-discovery.json")
        ec006 = next(row for row in gaps["scenarios"] if row["id"] == "EC-EVAL-006_INTERACTION_FAILURE_AND_BOUNDED_COMBINATORICS")
        criteria = " ".join(
            load_fixture("semantic-evaluation-rubric.json")["scenarios"][ec006["id"]]["criteria"]
        )
        supplied = " ".join(ec006["input"]["components"] + ec006["input"]["material_dimensions"])
        self.assertIn("Otherwise use `FULL`", reasoning)
        self.assertIn("automated reconciliation through stable client_reference", supplied)
        self.assertIn("operator-visible uncertain-state recovery", supplied)
        self.assertNotIn("FULL", ec006["review_task"])
        self.assertNotIn("SELECTED_METHOD_INFEASIBLE", ec006["review_task"])
        self.assertIn("uses FULL method selection", criteria)
        self.assertIn("does not invent alternatives", criteria)

    def test_post_pr6_fidelity_behaviors_have_clean_scenario_and_evaluator_coverage(self):
        controls = load_fixture("control-boundary-semantics.json")
        gaps = load_fixture("scenario-driven-gap-discovery.json")
        rubric = load_fixture("semantic-evaluation-rubric.json")
        ec004 = next(row for row in controls["scenarios"] if row["id"] == "EC-EVAL-004_VALIDATOR_PASS_IS_NOT_SEMANTIC_PROOF")
        ec006 = next(row for row in gaps["scenarios"] if row["id"] == "EC-EVAL-006_INTERACTION_FAILURE_AND_BOUNDED_COMBINATORICS")
        ec004_facts = " ".join(ec004["input"]["assessment"])
        ec006_facts = " ".join(ec006["input"]["components"] + ec006["input"]["material_dimensions"])
        ec004_criteria = " ".join(rubric["scenarios"][ec004["id"]]["criteria"])
        ec006_criteria = " ".join(rubric["scenarios"][ec006["id"]]["criteria"])

        self.assertIn("non-technical Persian-speaking Owner", ec004_facts)
        self.assertIn("does not state the exact resulting Head", ec004_facts)
        self.assertIn("request/intake", ec004_criteria)
        self.assertIn("planned-versus-actual deviations", ec004_criteria)
        self.assertIn("Persian-first delivery", ec004_criteria)
        self.assertNotIn("Persian-first", ec004["review_task"])
        self.assertNotIn("request/intake", ec004["review_task"])

        self.assertIn("stronger directly testable uncertainty resolution", ec006_facts)
        self.assertIn("lower implementation burden/time", ec006_facts)
        self.assertIn("canonical order of consideration", ec006_criteria)
        self.assertIn("without numeric weighting", ec006_criteria)
        self.assertNotIn("order of consideration", ec006["review_task"])
        self.assertNotIn("weighted scoring", ec006["review_task"])

    def test_post_pr7_remaining_coverage_gaps_are_falsifiable_without_answer_leakage(self):
        controls = load_fixture("control-boundary-semantics.json")
        gaps = load_fixture("scenario-driven-gap-discovery.json")
        rubric = load_fixture("semantic-evaluation-rubric.json")
        tasks = reviewer_tasks()
        controls_by_id = {row["id"]: row for row in controls["scenarios"]}
        gaps_by_id = {row["id"]: row for row in gaps["scenarios"]}

        ec009 = controls_by_id["EC-EVAL-009_PACKAGE_REVISION_STALENESS"]
        ec007 = gaps_by_id["EC-EVAL-007_DRIFT_MODEL_COMPLETENESS_AND_STOP"]
        ec008 = gaps_by_id["EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING"]
        ec009_facts = " ".join(ec009["input"]["package_state"])
        ec007_facts = " ".join(ec007["input"]["authority_and_surfaces"] + ec007["input"]["uninspected_context"])
        ec008_facts = " ".join(ec008["input"]["initial_evidence"] + ec008["input"]["fresh_owner_context"] + ec008["input"]["possible_future_changes"])
        ec009_criteria = " ".join(rubric["scenarios"][ec009["id"]]["criteria"])
        ec007_criteria = " ".join(rubric["scenarios"][ec007["id"]]["criteria"])
        ec008_criteria = " ".join(rubric["scenarios"][ec008["id"]]["criteria"])

        self.assertIn("accepted repository revision EC-A", ec009_facts)
        self.assertIn("canonical main has subsequently advanced to accepted revision EC-B", ec009_facts)
        self.assertIn("historical/version-bound artifact", ec009_criteria)
        self.assertIn("package structural/source-hash validity", ec009_criteria)
        self.assertIn("package rebuild/requalification", ec009_criteria)
        self.assertNotIn("historical/version-bound artifact", tasks[ec009["id"]])
        self.assertNotIn("package rebuild/requalification", tasks[ec009["id"]])

        self.assertIn("legacy test still requires JPG-only uploads", ec007_facts)
        self.assertIn("non-capability-shaped contract/test-drift finding", ec007_criteria)
        self.assertNotIn("MISSING_CAPABILITY", tasks[ec007["id"]])
        self.assertIn("repeatedly co-change after contract updates", ec007_facts)
        self.assertIn("manual-copy/co-change lifecycle mechanism", ec007_criteria)
        self.assertIn("rejects synchronizing only today's visible status literals as defect-class closure", ec007_criteria)
        self.assertIn("mobile-client status behavior", ec007_criteria)
        self.assertIn("NOT_PROVEN", ec007_criteria)
        self.assertNotIn("manual-copy/co-change lifecycle mechanism", tasks[ec007["id"]])
        self.assertNotIn("defect-class closure", tasks[ec007["id"]])

        self.assertIn("No prior independent review has been performed", ec008_facts)
        self.assertIn("does not request it ceremonially", ec008_criteria)
        self.assertIn("does not generalize this into a rule to never seek independent review", ec008_criteria)
        self.assertNotIn("ceremonially", tasks[ec008["id"]])
        self.assertIn("duplicate customer charges", ec008_facts)
        self.assertIn("next-day reconciliation", ec008_facts)
        self.assertIn("stronger preventive control is justified before deployment", ec008_criteria)
        self.assertIn("minimum effective forced control", ec008_criteria)
        self.assertIn("'stronger is always safer'", ec008_criteria)
        self.assertNotIn("stronger preventive control", tasks[ec008["id"]])
        self.assertNotIn("minimum effective forced control", tasks[ec008["id"]])

    def test_method_comparison_priority_contract(self):
        reasoning = (ROOT / "docs" / "core" / "REASONING_MODEL.md").read_text(encoding="utf-8")
        ordered = (
            "functional correctness / truthfulness",
            "defect-class closure / durability",
            "regression preservation / semantic blast radius",
            "authority / SSOT coherence / drift resistance",
            "falsifiability / proof strength",
            "proportionality / minimum effective control",
            "Owner operability / automation implications",
            "implementation / migration burden",
            "implementation time",
        )
        positions = [reasoning.index(fragment) for fragment in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("order of consideration, not a weighted scoring model", reasoning)
        self.assertIn("do not manufacture alternatives", reasoning.lower())
        self.assertIn("do not force a winner", reasoning)
        self.assertIn("Time remains relevant, but it must not silently outrank correctness or defect-class closure", reasoning)

    def test_post_implementation_report_contract_is_complete(self):
        reasoning = (ROOT / "docs" / "core" / "REASONING_MODEL.md").read_text(encoding="utf-8")
        required = (
            "what was actually implemented",
            "selected-method conformance is `PROVEN` or `NOT_PROVEN`",
            "focused falsification/test results",
            "affected regression results",
            "exact-Head CI/current verification status",
            "fresh rereview status where required",
            "remaining blockers or unknowns",
            "planned-versus-actual deviations",
            "exact resulting target identity / resulting Head",
            "executed evidence versus unavailable or unverified evidence",
        )
        for fragment in required:
            self.assertIn(fragment, reasoning)
        self.assertIn("Implementation success does not imply validation success", reasoning)
        self.assertIn("CI success does not imply rereview, merge/release, or Owner authorization", reasoning)

    def test_full_lifecycle_stage_separation_is_canonical(self):
        reasoning = (ROOT / "docs" / "core" / "REASONING_MODEL.md").read_text(encoding="utf-8")
        protocol = (ROOT / "docs" / "governance" / "REVIEW_PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn(
            "request / intake ≠ evidence ≠ assessment ≠ decision ≠ validation ≠ completion ≠ Owner delivery",
            reasoning,
        )
        self.assertIn("Receiving a request is not evidence", reasoning)
        self.assertIn("technical completion is not Owner-facing delivery or Owner authorization", reasoning)
        self.assertIn("not a lifecycle state machine or workflow engine", reasoning)
        self.assertIn("completion or PASS of one stage does not itself prove the next", protocol)

    def test_owner_facing_delivery_contract_is_distinct_and_persian_first(self):
        protocol = (ROOT / "docs" / "governance" / "REVIEW_PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("## Owner-facing delivery", protocol)
        self.assertIn("Persian-first by default", protocol)
        self.assertIn("distinct from the evidence-dense technical review and from any Executor prompt", protocol)
        for fragment in (
            "bounded decision/readiness state",
            "practical meaning",
            "confirmed root cause in plain language",
            "selected direction",
            "remaining blocker or unknown",
            "exact next action",
        ):
            self.assertIn(fragment, protocol)
        self.assertIn("technical Executor prompts may remain English", protocol)
        self.assertIn("do not duplicate the full technical review", protocol)


if __name__ == "__main__":
    unittest.main()