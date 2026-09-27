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
]
EVALUATOR_RUBRIC = "fixtures/semantic-evaluation-rubric.json"

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
    ".github/workflows/verify.yml",
]

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ENTRYPOINT_PHASE_RE = re.compile(r"^Repository phase:\s*`([^`]+)`\s*$", re.MULTILINE)
FORBIDDEN_REVIEWER_KEYS = {
    "expected_reasoning",
    "forbidden_shortcuts",
    "acceptable_final_states",
    "expected_answer",
    "expected_answers",
    "evaluator_criteria",
    "verdict",
}


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


def _contains_forbidden_reviewer_key(value) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_REVIEWER_KEYS:
                return key
            found = _contains_forbidden_reviewer_key(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _contains_forbidden_reviewer_key(child)
            if found:
                return found
    return None


def _scenario_id(value, label: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string", errors)
        return None
    return value


def check_semantic_evaluation_fixtures(errors: list[str]) -> None:
    scenario_ids: set[str] = set()

    gravity = load_json(SCENARIO_FIXTURES[0], errors)
    if isinstance(gravity, dict):
        if gravity.get("authority") != "NON_CANONICAL_EVALUATION_SCENARIO":
            fail("Gravity Flow scenario authority must be NON_CANONICAL_EVALUATION_SCENARIO", errors)
        sid = _scenario_id(gravity.get("id"), "Gravity Flow scenario id", errors)
        if sid:
            scenario_ids.add(sid)
        if not isinstance(gravity.get("scenario"), dict):
            fail("Gravity Flow scenario must contain a scenario object", errors)
        if not isinstance(gravity.get("review_task"), str) or not gravity["review_task"].strip():
            fail("Gravity Flow scenario must contain a non-empty review_task", errors)
        forbidden = _contains_forbidden_reviewer_key(gravity)
        if forbidden:
            fail(f"reviewer-input Gravity Flow scenario leaks evaluator key: {forbidden}", errors)

    controls = load_json(SCENARIO_FIXTURES[1], errors)
    if isinstance(controls, dict):
        if controls.get("authority") != "NON_CANONICAL_EVALUATION_SCENARIOS":
            fail("control-boundary scenario authority must be NON_CANONICAL_EVALUATION_SCENARIOS", errors)
        rows = controls.get("scenarios")
        if not isinstance(rows, list) or not rows:
            fail("control-boundary scenarios must be a non-empty list", errors)
        else:
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    fail(f"control-boundary scenario[{index}] must be an object", errors)
                    continue
                sid = _scenario_id(row.get("id"), f"control-boundary scenario[{index}].id", errors)
                if sid:
                    if sid in scenario_ids:
                        fail(f"duplicate semantic scenario id: {sid}", errors)
                    scenario_ids.add(sid)
                if not isinstance(row.get("input"), dict):
                    fail(f"control-boundary scenario[{index}] must contain an input object", errors)
                if not isinstance(row.get("review_task"), str) or not row["review_task"].strip():
                    fail(f"control-boundary scenario[{index}] must contain a non-empty review_task", errors)
        forbidden = _contains_forbidden_reviewer_key(controls)
        if forbidden:
            fail(f"reviewer-input control scenario leaks evaluator key: {forbidden}", errors)

    rubric = load_json(EVALUATOR_RUBRIC, errors)
    if not isinstance(rubric, dict):
        return
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
    print("- local Markdown links: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
