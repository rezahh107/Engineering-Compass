#!/usr/bin/env python3
"""Structural verifier for the Engineering Compass repository."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PHASE = "BASELINE_COMPLETE"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

SCENARIO_FIXTURES = [
    "fixtures/gravity-flow-version-coupling.json",
    "fixtures/control-boundary-semantics.json",
    "fixtures/scenario-driven-gap-discovery.json",
]
EVALUATOR_RUBRIC = "fixtures/semantic-evaluation-rubric.json"

GRAVITY_FIXTURE_KEYS = frozenset({"id", "authority", "purpose", "scope", "scenario", "review_task"})
GRAVITY_SCENARIO_KEYS = frozenset({"product", "upstream", "implementation_decisions", "local_performance_detail"})
GRAVITY_UPSTREAM_KEYS = frozenset({"name", "properties"})
CONTROL_FIXTURE_KEYS = frozenset({"authority", "purpose", "scenarios"})
CONTROL_SCENARIO_KEYS = frozenset({"id", "input", "review_task"})
CONTROL_INPUT_KEYS = {
    "EC-EVAL-002_REPOSITORY_CODE_IS_NOT_EXECUTION": frozenset({"repository_state", "claim_under_review"}),
    "EC-EVAL-003_MODEL_MEDIATED_IS_NOT_FORCED_PATH": frozenset({"workflow", "claim_under_review"}),
    "EC-EVAL-004_VALIDATOR_PASS_IS_NOT_SEMANTIC_PROOF": frozenset({"assessment", "claim_under_review"}),
    "EC-EVAL-009_PACKAGE_REVISION_STALENESS": frozenset({"package_state", "claim_under_review"}),
}
GAP_FIXTURE_KEYS = frozenset({"authority", "purpose", "scenarios"})
GAP_SCENARIO_KEYS = frozenset({"id", "input", "review_task"})
GAP_INPUT_KEYS = {
    "EC-EVAL-005_WORKFLOW_UNCERTAIN_OUTCOME": frozenset({"scope", "change", "known_evidence", "owner_authority"}),
    "EC-EVAL-006_INTERACTION_FAILURE_AND_BOUNDED_COMBINATORICS": frozenset({"scope", "components", "material_dimensions"}),
    "EC-EVAL-007_DRIFT_MODEL_COMPLETENESS_AND_STOP": frozenset({"scope", "authority_and_surfaces", "uninspected_context"}),
    "EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING": frozenset(
        {"scope", "initial_evidence", "fresh_owner_context", "possible_future_changes"}
    ),
    "EC-EVAL-010_REVIEW_TO_HANDOFF_FIDELITY": frozenset(
        {"scope", "review_context", "observed_evidence", "delivery_context"}
    ),
}
GAP_LIST_FIELDS = {
    "EC-EVAL-005_WORKFLOW_UNCERTAIN_OUTCOME": frozenset({"change", "known_evidence", "owner_authority"}),
    "EC-EVAL-006_INTERACTION_FAILURE_AND_BOUNDED_COMBINATORICS": frozenset({"components", "material_dimensions"}),
    "EC-EVAL-007_DRIFT_MODEL_COMPLETENESS_AND_STOP": frozenset({"authority_and_surfaces", "uninspected_context"}),
    "EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING": frozenset(
        {"initial_evidence", "fresh_owner_context", "possible_future_changes"}
    ),
    "EC-EVAL-010_REVIEW_TO_HANDOFF_FIDELITY": frozenset(
        {"review_context", "observed_evidence", "delivery_context"}
    ),
}
VALID_REVIEW_SCOPES = frozenset({"PR_SCOPE", "REPOSITORY_SCOPE"})

LEGACY_SEMANTIC_SCENARIO_IDS = frozenset(
    {
        "EC-EVAL-001_GRAVITY_FLOW_VERSION_COUPLING",
        "EC-EVAL-002_REPOSITORY_CODE_IS_NOT_EXECUTION",
        "EC-EVAL-003_MODEL_MEDIATED_IS_NOT_FORCED_PATH",
        "EC-EVAL-004_VALIDATOR_PASS_IS_NOT_SEMANTIC_PROOF",
        "EC-EVAL-005_WORKFLOW_UNCERTAIN_OUTCOME",
        "EC-EVAL-006_INTERACTION_FAILURE_AND_BOUNDED_COMBINATORICS",
        "EC-EVAL-007_DRIFT_MODEL_COMPLETENESS_AND_STOP",
        "EC-EVAL-008_OWNER_CONTEXT_RECLASSIFICATION_AND_ANTI_OVERENGINEERING",
        "EC-EVAL-009_PACKAGE_REVISION_STALENESS",
    }
)
REVIEW_TO_HANDOFF_SCENARIO_ID = "EC-EVAL-010_REVIEW_TO_HANDOFF_FIDELITY"
REVIEW_TO_HANDOFF_LEAKAGE_MARKERS = (
    "unique textual match ≠ native-control provenance",
    "does not fabricate alternative repair families",
    "emits a separate copy-ready executor prompt",
    "uses `bounded` when the supplied facts support",
)
REVIEW_TO_HANDOFF_PROTOCOL_MARKERS = (
    "A prompt-required delegated route is an incomplete handoff",
    "same response",
    "When `BOUNDED` is selected for a material repair",
    "Do not invent alternatives.",
    "Do not derive merge-blocking mechanically from finding severity",
    "version-/runtime-bounded",
    "three logically distinct surfaces",
    "## پرامپت اقدام",
    "[IMPLEMENTATION CONTRACT]",
    "[VALIDATION CONTRACT]",
    "[POST-IMPLEMENTATION REPORT]",
)
REVIEW_TO_HANDOFF_REASONING_MARKERS = (
    "Finding → Root-Cause Anchor → Root-Cause Qualification",
    "do not generate a repair prompt",
    "Selected Method Conformance Lock",
    "[IMPLEMENTATION CONTRACT]",
    "[VALIDATION CONTRACT]",
    "[POST-IMPLEMENTATION REPORT]",
)
REVIEW_TO_HANDOFF_VERIFICATION_MARKERS = (
    "review-to-handoff canonical/exact-marker synchronization remains intact",
    "complete reviewer-visible EC-EVAL-010 payload",
    "does not detect paraphrased or semantically equivalent leakage",
    "does not prove semantic engineering correctness, LLM compliance, or successful clean-context semantic evaluation",
)

REQUIRED = [
    "README.md",
    "AGENT_ENTRYPOINT.md",
    "AGENTS.md",
    "repository.manifest.json",
    "docs/core/MISSION.md",
    "docs/core/REASONING_MODEL.md",
    "docs/governance/AUTHORITY.md",
    "docs/governance/REVIEW_PROTOCOL.md",
    "docs/governance/VERIFICATION.md",
    "docs/research/RESEARCH_BASIS.md",
    "docs/decisions/ADR-0001-reasoning-orchestration.md",
    *SCENARIO_FIXTURES,
    EVALUATOR_RUBRIC,
    "scripts/verify_repo.py",
    "tests/test_semantic_fixture_contract.py",
    ".github/workflows/verify.yml",
]

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ENTRYPOINT_PHASE_RE = re.compile(r"^Repository phase:\s*`([^`]+)`\s*$", re.MULTILINE)


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def check_required(errors: list[str]) -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            fail(f"missing required path: {rel}", errors)


def load_json(rel: str, errors: list[str]):
    path = ROOT / rel
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON {rel}: {exc}", errors)
        return None


def _check_exact_keys(value: dict, expected: frozenset[str], label: str, errors: list[str]) -> None:
    actual = set(value)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        fail(f"{label} missing required fields: {missing}", errors)
    if unexpected:
        fail(f"{label} contains unsupported fields: {unexpected}", errors)


def _check_non_empty_string(value, label: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string", errors)
        return False
    return True


def _check_string_list(value, label: str, errors: list[str]) -> bool:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        fail(f"{label} must be a non-empty list of non-empty strings", errors)
        return False
    return True


def _complete_reviewer_payload_text(fixture: dict, scenario: dict) -> str:
    """Serialize exactly the reviewer-visible fixture metadata plus one scenario row."""
    return json.dumps(
        {
            "authority": fixture.get("authority"),
            "purpose": fixture.get("purpose"),
            "scenario": scenario,
        },
        ensure_ascii=False,
        sort_keys=True,
    ).lower()


def check_lifecycle(data: dict, errors: list[str]) -> None:
    repo = data.get("repository", {})
    phase = repo.get("phase")
    if phase != EXPECTED_PHASE:
        fail(f"manifest repository.phase must be {EXPECTED_PHASE}", errors)

    if phase == "BASELINE_COMPLETE":
        acceptance = data.get("acceptance")
        if not isinstance(acceptance, dict):
            fail("manifest acceptance must be an object", errors)
        else:
            baseline = acceptance.get("accepted_baseline")
            if not isinstance(baseline, dict):
                fail("manifest accepted baseline metadata is required", errors)
            else:
                for key in ("main_commit_sha", "tree_sha"):
                    value = baseline.get(key)
                    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
                        fail(f"manifest accepted_baseline.{key} must be a 40-character lowercase SHA", errors)
                source = baseline.get("acceptance_source")
                if not isinstance(source, str) or not source.strip():
                    fail("manifest accepted_baseline.acceptance_source must be non-empty", errors)

    entrypoint = (ROOT / "AGENT_ENTRYPOINT.md").read_text(encoding="utf-8")
    match = ENTRYPOINT_PHASE_RE.search(entrypoint)
    if match is None:
        fail("AGENT_ENTRYPOINT.md must declare Repository phase", errors)
    elif match.group(1) != phase:
        fail("AGENT_ENTRYPOINT.md repository phase contradicts manifest", errors)


def check_manifest(errors: list[str]) -> None:
    data = load_json("repository.manifest.json", errors)
    if not isinstance(data, dict):
        return

    repo = data.get("repository", {})
    if repo.get("name") != "Engineering-Compass":
        fail("manifest repository.name must be Engineering-Compass", errors)

    check_lifecycle(data, errors)

    surfaces = data.get("canonical_surfaces", {})
    if not isinstance(surfaces, dict) or not surfaces:
        fail("manifest canonical_surfaces must be a non-empty object", errors)
    else:
        for name, rel in surfaces.items():
            if not isinstance(rel, str) or not (ROOT / rel).exists():
                fail(f"manifest canonical surface does not resolve: {name} -> {rel}", errors)

    command = data.get("verification", {}).get("canonical_command")
    if command != "python3 scripts/verify_repo.py":
        fail("manifest canonical verification command drifted", errors)

    fixtures = data.get("fixtures", {})
    if not isinstance(fixtures, dict):
        fail("manifest fixtures must be an object", errors)
    else:
        if fixtures.get("semantic_regression_scenarios") != SCENARIO_FIXTURES:
            fail("manifest semantic_regression_scenarios must match canonical scenario fixtures", errors)
        if fixtures.get("semantic_evaluator_rubric") != EVALUATOR_RUBRIC:
            fail("manifest semantic_evaluator_rubric must match canonical evaluator rubric", errors)


def _scenario_id(value, label: str, errors: list[str]) -> str | None:
    if not _check_non_empty_string(value, label, errors):
        return None
    return value


def validate_gravity_reviewer_fixture(gravity: dict, errors: list[str]) -> str | None:
    _check_exact_keys(gravity, GRAVITY_FIXTURE_KEYS, "Gravity Flow reviewer fixture", errors)
    if gravity.get("authority") != "NON_CANONICAL_EVALUATION_SCENARIO":
        fail("Gravity Flow scenario authority must be NON_CANONICAL_EVALUATION_SCENARIO", errors)
    sid = _scenario_id(gravity.get("id"), "Gravity Flow scenario id", errors)
    _check_non_empty_string(gravity.get("purpose"), "Gravity Flow scenario purpose", errors)
    _check_non_empty_string(gravity.get("scope"), "Gravity Flow scenario scope", errors)
    _check_non_empty_string(gravity.get("review_task"), "Gravity Flow scenario review_task", errors)

    scenario = gravity.get("scenario")
    if not isinstance(scenario, dict):
        fail("Gravity Flow scenario must contain a scenario object", errors)
        return sid
    _check_exact_keys(scenario, GRAVITY_SCENARIO_KEYS, "Gravity Flow scenario payload", errors)
    _check_non_empty_string(scenario.get("product"), "Gravity Flow scenario product", errors)
    _check_string_list(scenario.get("implementation_decisions"), "Gravity Flow implementation_decisions", errors)
    _check_non_empty_string(scenario.get("local_performance_detail"), "Gravity Flow local_performance_detail", errors)

    upstream = scenario.get("upstream")
    if not isinstance(upstream, dict):
        fail("Gravity Flow scenario upstream must be an object", errors)
        return sid
    _check_exact_keys(upstream, GRAVITY_UPSTREAM_KEYS, "Gravity Flow upstream payload", errors)
    _check_non_empty_string(upstream.get("name"), "Gravity Flow upstream name", errors)
    _check_string_list(upstream.get("properties"), "Gravity Flow upstream properties", errors)
    return sid


def validate_control_reviewer_fixture(controls: dict, errors: list[str]) -> set[str]:
    _check_exact_keys(controls, CONTROL_FIXTURE_KEYS, "control-boundary reviewer fixture", errors)
    if controls.get("authority") != "NON_CANONICAL_EVALUATION_SCENARIOS":
        fail("control-boundary scenario authority must be NON_CANONICAL_EVALUATION_SCENARIOS", errors)
    _check_non_empty_string(controls.get("purpose"), "control-boundary scenario purpose", errors)

    scenario_ids: set[str] = set()
    rows = controls.get("scenarios")
    if not isinstance(rows, list) or not rows:
        fail("control-boundary scenarios must be a non-empty list", errors)
        return scenario_ids

    for index, row in enumerate(rows):
        label = f"control-boundary scenario[{index}]"
        if not isinstance(row, dict):
            fail(f"{label} must be an object", errors)
            continue
        _check_exact_keys(row, CONTROL_SCENARIO_KEYS, label, errors)
        sid = _scenario_id(row.get("id"), f"{label}.id", errors)
        if sid:
            if sid in scenario_ids:
                fail(f"duplicate semantic scenario id: {sid}", errors)
            scenario_ids.add(sid)
        _check_non_empty_string(row.get("review_task"), f"{label}.review_task", errors)

        scenario_input = row.get("input")
        if not isinstance(scenario_input, dict):
            fail(f"{label} must contain an input object", errors)
            continue
        expected_input_keys = CONTROL_INPUT_KEYS.get(sid)
        if expected_input_keys is None:
            fail(f"{label} id is not admitted by the reviewer-input contract: {sid!r}", errors)
            continue
        _check_exact_keys(scenario_input, expected_input_keys, f"{label}.input", errors)
        _check_non_empty_string(scenario_input.get("claim_under_review"), f"{label}.input.claim_under_review", errors)
        list_key = next(key for key in expected_input_keys if key != "claim_under_review")
        _check_string_list(scenario_input.get(list_key), f"{label}.input.{list_key}", errors)
    return scenario_ids


def validate_gap_reviewer_fixture(gaps: dict, errors: list[str]) -> set[str]:
    _check_exact_keys(gaps, GAP_FIXTURE_KEYS, "gap-discovery reviewer fixture", errors)
    if gaps.get("authority") != "NON_CANONICAL_EVALUATION_SCENARIOS":
        fail("gap-discovery scenario authority must be NON_CANONICAL_EVALUATION_SCENARIOS", errors)
    _check_non_empty_string(gaps.get("purpose"), "gap-discovery scenario purpose", errors)

    scenario_ids: set[str] = set()
    rows = gaps.get("scenarios")
    if not isinstance(rows, list) or not rows:
        fail("gap-discovery scenarios must be a non-empty list", errors)
        return scenario_ids

    for index, row in enumerate(rows):
        label = f"gap-discovery scenario[{index}]"
        if not isinstance(row, dict):
            fail(f"{label} must be an object", errors)
            continue
        _check_exact_keys(row, GAP_SCENARIO_KEYS, label, errors)
        sid = _scenario_id(row.get("id"), f"{label}.id", errors)
        if sid:
            if sid in scenario_ids:
                fail(f"duplicate semantic scenario id: {sid}", errors)
            scenario_ids.add(sid)
        _check_non_empty_string(row.get("review_task"), f"{label}.review_task", errors)

        scenario_input = row.get("input")
        if not isinstance(scenario_input, dict):
            fail(f"{label} must contain an input object", errors)
            continue
        expected_input_keys = GAP_INPUT_KEYS.get(sid)
        if expected_input_keys is None:
            fail(f"{label} id is not admitted by the reviewer-input contract: {sid!r}", errors)
            continue
        _check_exact_keys(scenario_input, expected_input_keys, f"{label}.input", errors)

        scope = scenario_input.get("scope")
        if scope not in VALID_REVIEW_SCOPES:
            fail(f"{label}.input.scope must be one of {sorted(VALID_REVIEW_SCOPES)}", errors)
        for field in GAP_LIST_FIELDS[sid]:
            _check_string_list(scenario_input.get(field), f"{label}.input.{field}", errors)

        if sid == REVIEW_TO_HANDOFF_SCENARIO_ID:
            reviewer_payload = _complete_reviewer_payload_text(gaps, row)
            for marker in REVIEW_TO_HANDOFF_LEAKAGE_MARKERS:
                if marker.lower() in reviewer_payload:
                    fail(
                        f"{label} complete reviewer-visible payload leaks evaluator-only answer marker: {marker}",
                        errors,
                    )
    return scenario_ids


def validate_evaluator_rubric(rubric: dict, scenario_ids: set[str], errors: list[str]) -> None:
    if rubric.get("authority") != "EVALUATOR_ONLY_NON_CANONICAL":
        fail("semantic evaluator rubric authority must be EVALUATOR_ONLY_NON_CANONICAL", errors)
    if rubric.get("result_states") != ["PASS", "FAIL", "NOT_PROVEN"]:
        fail("semantic evaluator rubric result_states must be PASS/FAIL/NOT_PROVEN", errors)
    if not isinstance(rubric.get("reviewer_input_rule"), str) or not rubric["reviewer_input_rule"].strip():
        fail("semantic evaluator rubric must declare reviewer_input_rule", errors)
    if not isinstance(rubric.get("global_criteria"), list) or not rubric["global_criteria"]:
        fail("semantic evaluator rubric must contain global_criteria", errors)

    rubric_scenarios = rubric.get("scenarios")
    if not isinstance(rubric_scenarios, dict):
        fail("semantic evaluator rubric scenarios must be an object", errors)
        return

    rubric_ids = set(rubric_scenarios)
    if rubric_ids != scenario_ids:
        missing = sorted(scenario_ids - rubric_ids)
        extra = sorted(rubric_ids - scenario_ids)
        fail(f"semantic scenario/rubric ids differ; missing={missing}, extra={extra}", errors)

    for sid, spec in rubric_scenarios.items():
        if not isinstance(spec, dict):
            fail(f"rubric scenario {sid} must be an object", errors)
            continue
        criteria = spec.get("criteria")
        if not isinstance(criteria, list) or not criteria or not all(isinstance(item, str) and item.strip() for item in criteria):
            fail(f"rubric scenario {sid} must contain non-empty string criteria", errors)


def check_semantic_evaluation_fixtures(errors: list[str]) -> None:
    scenario_ids: set[str] = set()

    gravity = load_json(SCENARIO_FIXTURES[0], errors)
    if isinstance(gravity, dict):
        sid = validate_gravity_reviewer_fixture(gravity, errors)
        if sid:
            scenario_ids.add(sid)

    controls = load_json(SCENARIO_FIXTURES[1], errors)
    if isinstance(controls, dict):
        for sid in validate_control_reviewer_fixture(controls, errors):
            if sid in scenario_ids:
                fail(f"duplicate semantic scenario id: {sid}", errors)
            scenario_ids.add(sid)

    gaps = load_json(SCENARIO_FIXTURES[2], errors)
    if isinstance(gaps, dict):
        for sid in validate_gap_reviewer_fixture(gaps, errors):
            if sid in scenario_ids:
                fail(f"duplicate semantic scenario id: {sid}", errors)
            scenario_ids.add(sid)

    missing_legacy = sorted(LEGACY_SEMANTIC_SCENARIO_IDS - scenario_ids)
    if missing_legacy:
        fail(f"existing EC-EVAL-001..009 scenarios must remain intact; missing={missing_legacy}", errors)
    if REVIEW_TO_HANDOFF_SCENARIO_ID not in scenario_ids:
        fail(f"review-to-handoff semantic scenario missing: {REVIEW_TO_HANDOFF_SCENARIO_ID}", errors)

    rubric = load_json(EVALUATOR_RUBRIC, errors)
    if isinstance(rubric, dict):
        validate_evaluator_rubric(rubric, scenario_ids, errors)


def check_review_to_handoff_contract(errors: list[str]) -> None:
    protocol = (ROOT / "docs" / "governance" / "REVIEW_PROTOCOL.md").read_text(encoding="utf-8")
    reasoning = (ROOT / "docs" / "core" / "REASONING_MODEL.md").read_text(encoding="utf-8")
    verification = (ROOT / "docs" / "governance" / "VERIFICATION.md").read_text(encoding="utf-8")

    for marker in REVIEW_TO_HANDOFF_PROTOCOL_MARKERS:
        if marker not in protocol:
            fail(f"review-to-handoff protocol marker missing: {marker}", errors)
    for marker in REVIEW_TO_HANDOFF_REASONING_MARKERS:
        if marker not in reasoning:
            fail(f"root-cause-to-prompt canonical marker missing: {marker}", errors)
    for marker in REVIEW_TO_HANDOFF_VERIFICATION_MARKERS:
        if marker not in verification:
            fail(f"review-to-handoff verification-boundary marker missing: {marker}", errors)


def is_external_link(target: str) -> bool:
    lowered = target.lower()
    return lowered.startswith(
        ("http://", "https://", "mailto:", "tel:", "#", "data:")
    )


def check_markdown_links(errors: list[str]) -> None:
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or is_external_link(target):
                continue
            target = target.split(" ", 1)[0].strip("<>")
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                fail(f"link escapes repository: {path.relative_to(ROOT)} -> {target}", errors)
                continue
            if not resolved.exists():
                fail(f"broken local link: {path.relative_to(ROOT)} -> {target}", errors)


def check_agent_contract(errors: list[str]) -> None:
    expected = "python3 scripts/verify_repo.py"
    for rel in ["AGENTS.md", "docs/governance/VERIFICATION.md"]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        if expected not in text:
            fail(f"{rel} does not reference canonical verification command", errors)


def main() -> int:
    errors: list[str] = []
    check_required(errors)
    check_manifest(errors)
    check_semantic_evaluation_fixtures(errors)
    check_review_to_handoff_contract(errors)
    check_markdown_links(errors)
    check_agent_contract(errors)

    if errors:
        print("Engineering Compass verification: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Engineering Compass verification: PASS")
    print(f"- required paths: {len(REQUIRED)}")
    print("- repository.manifest.json: valid")
    print("- repository lifecycle metadata: consistent")
    print("- semantic scenario/rubric separation: valid")
    print("- review-to-handoff canonical/exact-marker synchronization: valid")
    print("- local Markdown links: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
