# Engineering Compass — Agent Instructions

Read [`AGENT_ENTRYPOINT.md`](AGENT_ENTRYPOINT.md) first.

Keep this file short; canonical semantics live in referenced docs.

## Before changing this repository

1. Read `repository.manifest.json` and the smallest relevant canonical/runtime docs.
2. Preserve the distinction between LLM judgment and deterministic enforcement.
3. Do not add a direct Finding→patch-prompt path.
4. Do not vendor or silently reconstruct Prompt-Pipeline rules; update the inspected lock deliberately when compatibility changes.
5. Add/update focused fixtures/tests for material runtime changes.
6. Run:

```bash
python3 scripts/verify_repo.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Completion boundary

Do not report repository/runtime verification as PASS unless the commands above ran on the exact resulting tree/Head and succeeded. Prompt-Pipeline generation state, CI state, LLM semantic correctness, implementation completion, and fresh rereview are separate claims.
