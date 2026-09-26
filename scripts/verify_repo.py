#!/usr/bin/env python3
"""Structural verifier for the Engineering Compass repository."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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
    "fixtures/gravity-flow-version-coupling.json",
    "scripts/verify_repo.py",
    ".github/workflows/verify.yml",
]

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

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

def check_manifest(errors: list[str]) -> None:
    data = load_json("repository.manifest.json", errors)
    if not isinstance(data, dict):
        return

    repo = data.get("repository", {})
    if repo.get("name") != "Engineering-Compass":
        fail("manifest repository.name must be Engineering-Compass", errors)

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

def check_fixture(errors: list[str]) -> None:
    data = load_json("fixtures/gravity-flow-version-coupling.json", errors)
    if not isinstance(data, dict):
        return

    for key in [
        "id",
        "authority",
        "scenario",
        "expected_reasoning",
        "forbidden_shortcuts",
        "acceptable_final_states",
    ]:
        if key not in data:
            fail(f"fixture missing required key: {key}", errors)

    if data.get("authority") != "NON_CANONICAL_TEST_SPEC":
        fail("fixture authority must remain NON_CANONICAL_TEST_SPEC", errors)

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
    check_fixture(errors)
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
    print("- semantic fixture JSON: valid")
    print("- local Markdown links: valid")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
