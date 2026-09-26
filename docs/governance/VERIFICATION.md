# Repository Verification Contract

## Canonical command

```bash
python3 scripts/verify_repo.py
```

Humans, agents, and CI should use the same underlying verifier.

## What the verifier checks

The current structural verifier checks:

- required Foundation files exist;
- `repository.manifest.json` is valid JSON;
- the canonical repository phase is `BASELINE_COMPLETE`;
- accepted-baseline metadata is present and SHA-shaped when the baseline is complete;
- `AGENT_ENTRYPOINT.md` reports the same repository phase as the canonical manifest;
- canonical manifest paths exist;
- semantic regression fixtures are valid JSON and contain required contract fields;
- local Markdown links resolve to repository files/directories;
- the agent entrypoints point to the canonical verification command.

## What it does not prove

A structural PASS does **not** prove:

- the recorded accepted-baseline metadata corresponds to remote GitHub history;
- an LLM will follow the guidance;
- the reasoning model is complete;
- a review will find every architecture defect;
- a fixture has been successfully executed against multiple models;
- production/runtime behavior of a reviewed external project;
- platform controls beyond what the workflow actually runs.

Guidance is `prompt_level_influence`; CI is deterministic only for the structural checks it executes.

## Semantic regression boundary

Fixtures under `fixtures/` define review behaviors that should be preserved.

In the current baseline-complete repository state they are **test specifications**, not an executable LLM evaluation harness.

A future model-evaluation runner may consume them, but until such a runner exists, report semantic regression as `NOT_EXECUTED` unless a human/model evaluation was actually performed.

## Exact-target qualification

For a repository change:

1. run the canonical command on the exact resulting tree/Head;
2. record actual output/exit status;
3. if CI is relevant, inspect the workflow result for the same commit;
4. do not call skipped/unavailable checks PASS;
5. report structural verification separately from semantic reasoning evaluation.

## Definition of Done for Foundation changes

A Foundation/document-governance change is structurally complete when:

- the canonical verifier passes on the exact candidate;
- internal links are valid;
- machine-readable artifacts parse;
- changed canonical semantics have been reflected in relevant fixtures or a reason is documented for no fixture change;
- agent instructions remain concise pointers rather than duplicated manuals;
- claims stay within the verification boundary.
