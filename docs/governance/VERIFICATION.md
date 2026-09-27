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
- semantic evaluation scenario fixtures and the evaluator-only rubric are valid JSON, use unique scenario IDs, and remain structurally separated;
- every evaluator-rubric scenario corresponds to an available reviewer-input scenario and vice versa;
- local Markdown links resolve to repository files/directories;
- the agent entrypoints point to the canonical verification command.

## What it does not prove

A structural PASS does **not** prove:

- the recorded accepted-baseline metadata corresponds to remote GitHub history;
- an LLM will follow the guidance;
- repository-visible deterministic code was executed on a review path;
- a model-mediated instruction became an externally forced control;
- a schema/validator PASS establishes semantic engineering correctness;
- the reasoning model is complete;
- a review will find every architecture defect;
- a fixture has been successfully executed against any model;
- production/runtime behavior of a reviewed external project;
- platform controls beyond what the workflow actually runs.

Guidance is `prompt_level_influence`; deterministic validation proves only the predicates it actually executes. Mechanical-enforcement claims require evidence of an externally forced path and are limited to the exact predicates enforced on that path.

## Semantic regression boundary

Fixtures under `fixtures/` define behaviors that should be evaluated, but fixture existence is not an executed semantic evaluation.

Scenario input and evaluator expectations are physically separated:

- reviewer-model input comes from scenario fixtures such as `fixtures/gravity-flow-version-coupling.json` and `fixtures/control-boundary-semantics.json`;
- evaluator expectations live in `fixtures/semantic-evaluation-rubric.json` and must not be shown to the reviewer model during a clean-context run.

For an actual semantic comparison:

1. give a fresh reviewer model the applicable canonical Engineering Compass guidance plus only the scenario input;
2. record the reviewer response without exposing the evaluator rubric;
3. only after that response is complete, evaluate it against the rubric;
4. preserve per-scenario `PASS`, `FAIL`, or `NOT_PROVEN` evidence with concise criterion-level reasons;
5. do not collapse the scenarios into an opaque numeric score;
6. distinguish the observed run from any broader claim about model compliance.

A clean-context model run proves only the behavior observed in that run. If no genuinely independent clean-context evaluation is available, report `SEMANTIC_EVAL_NOT_EXECUTED` rather than using already-informed reasoning as evidence of improvement.

## Guidance / Validation / Proof reporting

For a claimed control, report enough to distinguish:

- **Guidance** — repository-visible instruction/artifact; no execution claim follows from existence alone.
- **Validation** — an actually executed check and the exact predicate(s) it established, plus what it did not establish.
- **Proof of mechanical control** — an externally forced consumer/gate actually executed the control and bypass was excluded within the claimed boundary.

A validator claim should identify the failure prevented, machine-checkable predicate when applicable, executor, consumer, and bypass possibility. Claim strength must not exceed that evidence.

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
- changed canonical semantics have been reflected in relevant evaluation scenarios/rubric or a reason is documented for no fixture change;
- agent instructions remain concise pointers rather than duplicated manuals;
- claims stay within the verification boundary.
