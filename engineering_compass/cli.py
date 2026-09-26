from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .github_evidence import GitHubEvidenceCollector
from .model import ContractError, validate_request
from .projection import project_action
from .prompt_pipeline import build_prompt_pipeline_intake, run_prompt_pipeline, verify_prompt_pipeline_checkout, write_intake


def _read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str, value: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="engineering-compass")
    sub = parser.add_subparsers(dest="command", required=True)

    collect = sub.add_parser("collect", help="Collect exact target evidence from GitHub")
    collect.add_argument("--request", required=True)
    collect.add_argument("--out", required=True)

    project = sub.add_parser("project", help="Validate assessment and project canonical next action")
    project.add_argument("--evidence", required=True)
    project.add_argument("--assessment", required=True)
    project.add_argument("--out", required=True)

    handoff = sub.add_parser("prompt-handoff", help="Build Prompt-Pipeline canonical intake")
    handoff.add_argument("--evidence", required=True)
    handoff.add_argument("--assessment", required=True)
    handoff.add_argument("--out", required=True)

    prompt_check = sub.add_parser("prompt-check", help="Verify locked Prompt-Pipeline checkout identity and governing files")
    prompt_check.add_argument("--prompt-pipeline-root", required=True)
    prompt_check.add_argument("--out", required=True)

    compile_prompt = sub.add_parser("compile-prompt", help="Run locked external Prompt-Pipeline checkout")
    compile_prompt.add_argument("--intake", required=True)
    compile_prompt.add_argument("--prompt-pipeline-root", required=True)
    compile_prompt.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "collect":
            request = _read_json(args.request)
            validate_request(request)
            bundle = GitHubEvidenceCollector().collect(request)
            _write_json(args.out, bundle)
        elif args.command == "project":
            projection = project_action(_read_json(args.evidence), _read_json(args.assessment))
            _write_json(args.out, projection)
        elif args.command == "prompt-handoff":
            intake = build_prompt_pipeline_intake(_read_json(args.evidence), _read_json(args.assessment))
            write_intake(args.out, intake)
        elif args.command == "prompt-check":
            result = verify_prompt_pipeline_checkout(args.prompt_pipeline_root)
            _write_json(args.out, result)
        elif args.command == "compile-prompt":
            result = run_prompt_pipeline(args.intake, args.prompt_pipeline_root)
            _write_json(args.out, result)
        else:  # pragma: no cover
            parser.error("unknown command")
        return 0
    except (ContractError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Engineering Compass: BLOCKED: {exc}", file=sys.stderr)
        return 2
