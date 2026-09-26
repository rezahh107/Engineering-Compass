# Engineering Compass — Agent Instructions

Read [`AGENT_ENTRYPOINT.md`](AGENT_ENTRYPOINT.md) first.

Keep this file short. Canonical semantics live in the referenced docs, not here.

## Before changing this repository

1. Read `repository.manifest.json`.
2. Read the smallest relevant canonical docs.
3. Preserve the distinction between reasoning guidance and deterministic enforcement.
4. Do not turn the project into an encyclopedic checklist or duplicate general engineering knowledge.
5. For material reasoning/governance changes, update or add regression fixtures when the changed behavior can be represented.
6. Run the canonical verifier:

```bash
python3 scripts/verify_repo.py
```

## Completion boundary

Do not report repository verification as PASS unless the command above was run on the exact resulting tree/Head and succeeded. A passing structural verifier does not prove LLM reasoning quality.
