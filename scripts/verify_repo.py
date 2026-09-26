#!/usr/bin/env python3
"""Canonical repository/runtime verifier for Engineering Compass."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EXPECTED_PHASE = "BASELINE_COMPLETE"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ENTRYPOINT_PHASE_RE = re.compile(r"^Repository phase:\s*`([^`]+)`\s*$", re.MULTILINE)

REQUIRED = [
    "README.md", "AGENT_ENTRYPOINT.md", "AGENTS.md", "repository.manifest.json", "pyproject.toml",
    "docs/core/MISSION.md", "docs/core/REASONING_MODEL.md", "docs/governance/AUTHORITY.md",
    "docs/governance/REVIEW_PROTOCOL.md", "docs/governance/VERIFICATION.md", "docs/research/RESEARCH_BASIS.md",
    "docs/runtime/ARCHITECTURE.md", "docs/runtime/ROOT_CAUSE_REPAIR.md", "docs/runtime/ACTION_MODEL.md",
    "docs/runtime/PROMPT_PIPELINE.md", "docs/runtime/LLM_ASSESSMENT_CONTRACT.md",
    "docs/decisions/ADR-0001-reasoning-orchestration.md", "docs/decisions/ADR-0002-executable-review-control-plane.md",
    "engineering_compass/__init__.py", "engineering_compass/__main__.py", "engineering_compass/model.py",
    "engineering_compass/github_evidence.py", "engineering_compass/root_cause.py", "engineering_compass/projection.py",
    "engineering_compass/prompt_pipeline.py", "engineering_compass/cli.py",
    "schemas/review-request.schema.json", "schemas/evidence-bundle.schema.json", "schemas/assessment.schema.json",
    "schemas/action-projection.schema.json", "schemas/prompt-handoff.schema.json",
    "integrations/prompt-pipeline.lock.json", "fixtures/gravity-flow-version-coupling.json",
    "fixtures/runtime/repair-full.json", "fixtures/runtime/root-cause-unproven.json", "tests/test_runtime.py",
    "scripts/verify_repo.py", ".github/workflows/verify.yml",
]


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def load_json(rel: str, errors: list[str]):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON {rel}: {exc}", errors)
        return None


def check_required(errors: list[str]) -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            fail(f"missing required path: {rel}", errors)


def check_lifecycle(data: dict, errors: list[str]) -> None:
    repo = data.get("repository", {})
    phase = repo.get("phase")
    if phase != EXPECTED_PHASE:
        fail(f"manifest repository.phase must be {EXPECTED_PHASE}", errors)
    acceptance = data.get("acceptance", {})
    baseline = acceptance.get("accepted_baseline", {}) if isinstance(acceptance, dict) else {}
    for key in ("main_commit_sha", "tree_sha"):
        value = baseline.get(key)
        if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
            fail(f"manifest accepted_baseline.{key} must be lowercase SHA-40", errors)
    entrypoint = (ROOT / "AGENT_ENTRYPOINT.md").read_text(encoding="utf-8")
    match = ENTRYPOINT_PHASE_RE.search(entrypoint)
    if match is None:
        fail("AGENT_ENTRYPOINT.md must declare Repository phase", errors)
    elif match.group(1) != phase:
        fail("AGENT_ENTRYPOINT.md repository phase contradicts manifest", errors)


def check_manifest(errors: list[str]) -> None:
    data = load_json("repository.manifest.json", errors)
    if not isinstance(data, dict): return
    if data.get("repository", {}).get("name") != "Engineering-Compass":
        fail("manifest repository.name must be Engineering-Compass", errors)
    check_lifecycle(data, errors)
    surfaces = data.get("canonical_surfaces", {})
    if not isinstance(surfaces, dict) or not surfaces:
        fail("manifest canonical_surfaces must be non-empty", errors)
    else:
        for name, rel in surfaces.items():
            if not isinstance(rel, str) or not (ROOT / rel).exists():
                fail(f"manifest canonical surface does not resolve: {name} -> {rel}", errors)
    verification = data.get("verification", {})
    if verification.get("canonical_command") != "python3 scripts/verify_repo.py":
        fail("manifest canonical verification command drifted", errors)
    if verification.get("unit_test_command") != "python3 -m unittest discover -s tests -p 'test_*.py'":
        fail("manifest unit test command drifted", errors)
    if data.get("runtime", {}).get("prompt_pipeline_lock") != "integrations/prompt-pipeline.lock.json":
        fail("manifest Prompt-Pipeline lock path drifted", errors)


def check_json_contracts(errors: list[str]) -> None:
    for rel in [
        "schemas/review-request.schema.json", "schemas/evidence-bundle.schema.json", "schemas/assessment.schema.json",
        "schemas/action-projection.schema.json", "schemas/prompt-handoff.schema.json",
        "fixtures/runtime/repair-full.json", "fixtures/runtime/root-cause-unproven.json",
    ]:
        load_json(rel, errors)
    semantic = load_json("fixtures/gravity-flow-version-coupling.json", errors)
    if isinstance(semantic, dict):
        for key in ["id", "authority", "scenario", "expected_reasoning", "forbidden_shortcuts", "acceptable_final_states"]:
            if key not in semantic: fail(f"semantic fixture missing required key: {key}", errors)
        if semantic.get("authority") != "NON_CANONICAL_TEST_SPEC":
            fail("semantic fixture authority must remain NON_CANONICAL_TEST_SPEC", errors)


def check_prompt_pipeline_lock(errors: list[str]) -> None:
    lock = load_json("integrations/prompt-pipeline.lock.json", errors)
    if not isinstance(lock, dict): return
    if lock.get("source_repository") != "rezahh107/Prompt-Pipeline": fail("Prompt-Pipeline lock source repository drifted", errors)
    if not isinstance(lock.get("source_commit_sha"), str) or SHA_RE.fullmatch(lock["source_commit_sha"]) is None:
        fail("Prompt-Pipeline lock source_commit_sha must be SHA-40", errors)
    if lock.get("domain") != "prompt_generation" or lock.get("domain_version") != "2026.3":
        fail("Prompt-Pipeline active integration domain/version drifted", errors)
    files = lock.get("governing_files")
    if not isinstance(files, list) or not files:
        fail("Prompt-Pipeline lock governing_files must be non-empty", errors); return
    for index, item in enumerate(files):
        if not isinstance(item, dict): fail(f"Prompt-Pipeline governing file {index} invalid", errors); continue
        if not isinstance(item.get("path"), str) or not item["path"]: fail(f"Prompt-Pipeline governing file {index} path invalid", errors)
        if not isinstance(item.get("blob_sha"), str) or SHA_RE.fullmatch(item["blob_sha"]) is None:
            fail(f"Prompt-Pipeline governing file {index} blob_sha invalid", errors)


def check_runtime_fixtures(errors: list[str]) -> None:
    try:
        from engineering_compass.projection import project_action
        from engineering_compass.prompt_pipeline import build_prompt_pipeline_intake
    except Exception as exc:
        fail(f"cannot import runtime package: {exc}", errors); return
    for rel, expected in [("fixtures/runtime/repair-full.json", "IMPLEMENT_REPAIR"), ("fixtures/runtime/root-cause-unproven.json", "VERIFY_ROOT_CAUSE")]:
        data = load_json(rel, errors)
        if not isinstance(data, dict): continue
        try:
            projection = project_action(data["evidence"], data["assessment"])
        except Exception as exc:
            fail(f"runtime fixture {rel} failed validation/projection: {exc}", errors); continue
        if projection.get("action") != expected: fail(f"runtime fixture {rel} expected {expected}, got {projection.get('action')}", errors)
        if expected == "IMPLEMENT_REPAIR":
            try: intake = build_prompt_pipeline_intake(data["evidence"], data["assessment"])
            except Exception as exc: fail(f"runtime repair fixture cannot build Prompt-Pipeline intake: {exc}", errors); continue
            for required in ("Confirmed root cause", "Conformance lock", "Falsification obligations", "[IMPLEMENTATION CONTRACT]", "SELECTED_METHOD_INFEASIBLE"):
                if required not in intake.get("request", ""): fail(f"Prompt-Pipeline handoff missing invariant token: {required}", errors)


def is_external_link(target: str) -> bool:
    return target.lower().startswith(("http://", "https://", "mailto:", "tel:", "#", "data:"))


def check_markdown_links(errors: list[str]) -> None:
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts: continue
        for target in LINK_RE.findall(path.read_text(encoding="utf-8")):
            target = target.strip().split("#", 1)[0]
            if not target or is_external_link(target): continue
            target = target.split(" ", 1)[0].strip("<>")
            resolved = (path.parent / target).resolve()
            try: resolved.relative_to(ROOT.resolve())
            except ValueError: fail(f"link escapes repository: {path.relative_to(ROOT)} -> {target}", errors); continue
            if not resolved.exists(): fail(f"broken local link: {path.relative_to(ROOT)} -> {target}", errors)


def check_agent_contract(errors: list[str]) -> None:
    for rel in ["AGENTS.md", "AGENT_ENTRYPOINT.md", "docs/governance/VERIFICATION.md"]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for expected in ["python3 scripts/verify_repo.py", "python3 -m unittest discover -s tests -p 'test_*.py'"]:
            if expected not in text: fail(f"{rel} does not reference canonical command: {expected}", errors)


def main() -> int:
    errors: list[str] = []
    check_required(errors)
    if not errors:
        check_manifest(errors); check_json_contracts(errors); check_prompt_pipeline_lock(errors); check_runtime_fixtures(errors); check_markdown_links(errors); check_agent_contract(errors)
    if errors:
        print("Engineering Compass verification: FAIL")
        for error in errors: print(f"- {error}")
        return 1
    print("Engineering Compass verification: PASS")
    print(f"- required paths: {len(REQUIRED)}")
    print("- repository lifecycle and canonical surfaces: valid")
    print("- runtime contracts/fixtures: valid")
    print("- Prompt-Pipeline integration lock: structurally valid")
    print("- local Markdown links: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
