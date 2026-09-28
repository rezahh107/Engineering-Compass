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
- review-to-handoff canonical/exact-marker synchronization remains intact: required canonical protocol/root-cause markers are present, EC-EVAL-010 stays synchronized with its evaluator-rubric ID, and exact protected evaluator-only markers are rejected anywhere in the complete reviewer-visible EC-EVAL-010 payload (applicable fixture-level `authority`/`purpose` plus scenario content);
- final-gate strict canonical/exact-marker synchronization remains intact: required `FINAL_GATE_STRICT` protocol/reasoning-base markers are present, EC-EVAL-011 stays synchronized with its evaluator-rubric ID, and exact protected evaluator-only markers are rejected anywhere in the complete reviewer-visible EC-EVAL-011 payload (applicable fixture-level `authority`/`purpose` plus scenario content);
- local Markdown links resolve to repository files/directories;
- the agent entrypoints point to the canonical verification command.

The review-to-handoff predicate above is deliberately deterministic and exact-marker based. Its PASS proves only that the required canonical strings are present, the admitted scenario/rubric identities remain synchronized, and the protected exact markers are absent from the defined reviewer-visible payload. It does not detect paraphrased or semantically equivalent leakage and does not prove semantic engineering correctness, LLM compliance, or successful clean-context semantic evaluation.

The final-gate strict predicate above is likewise deliberately deterministic and exact-marker based. Its PASS proves only that the required `FINAL_GATE_STRICT` canonical strings are present, EC-EVAL-011 remains admitted and synchronized with its evaluator-rubric identity, and the protected exact evaluator-only markers are absent from the complete reviewer-visible EC-EVAL-011 payload. It does not detect paraphrased or semantically equivalent leakage and does not prove semantic engineering correctness, LLM compliance, successful clean-context semantic evaluation, or universal representation coverage.

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
- platform controls beyond what the workflow actually runs;
- a current PR review is still fresh after its Head changes;
- a package/retrieved Source was actually loaded or activated by an LLM.

Guidance is `prompt_level_influence`; deterministic validation proves only the predicates it actually executes. Mechanical-enforcement claims require evidence of an externally forced path and are limited to the exact predicates enforced on that path.

## Semantic regression boundary

Fixtures under `fixtures/` define behaviors that should be evaluated, but fixture existence is not an executed semantic evaluation.

Scenario input and evaluator expectations are physically separated:

- reviewer-model input comes from scenario fixtures such as `fixtures/gravity-flow-version-coupling.json`, `fixtures/control-boundary-semantics.json`, and `fixtures/scenario-driven-gap-discovery.json`;
- evaluator expectations live in `fixtures/semantic-evaluation-rubric.json` and must not be shown to the reviewer model during a clean-context run.

### Evaluator semantic-fidelity boundary

The evaluator rubric is a **non-canonical test artifact**. It may test canonical Engineering Compass behavior, but it must not introduce a new normative rule, authority precedence, product policy, decision-state mapping, or reasoning obligation absent from canonical guidance.

Every material evaluator criterion must be derivable from the applicable canonical guidance plus the scenario. When canonical semantics intentionally change, affected scenario/rubric expectations should migrate together.

A small deterministic synchronization assertion may protect a known source/rubric relationship, but it proves only that exact consistency predicate. It does not prove that the evaluator's interpretation is semantically complete, that the reviewer will follow the guidance, or that an LLM judgment is correct.

For an actual semantic comparison:

1. give a fresh reviewer model the applicable canonical Engineering Compass guidance plus only the scenario input;
2. record the reviewer response without exposing the evaluator rubric;
3. only after that response is complete, evaluate it against the rubric;
4. preserve per-scenario `PASS`, `FAIL`, or `NOT_PROVEN` evidence with concise criterion-level reasons;
5. do not collapse the scenarios into an opaque numeric score;
6. distinguish whether a rule existed, whether it activated, and whether activation materially improved the engineering decision;
7. distinguish the observed run from any broader claim about model compliance.

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

For `PR_SCOPE` review when current PR reality is decision-material, exact-target qualification should additionally preserve the reviewed repository/PR/Base/Head identity, changed-file inventory completeness, inspected diff/patch, and relevant check/review surfaces. A check display name is not sufficient producer identity when producer identity matters. Synthetic merge-ref evidence must not silently substitute for exact-Head evidence.

Before reporting a current GREEN/completion state, recheck live Head/freshness. If the target moved, mark only identity-dependent evidence stale, preserve identity-independent evidence, and rerun affected stages. No stale GREEN.

Missing access, pagination, producer identity, checks, or target freshness should block only conclusions that depend on that evidence. Preserve unaffected results and report the smallest recovery action. Never promote `UNKNOWN`, `MISSING`, `STALE`, `NOT_EXECUTED`, or unavailable checks to PASS.

## Repair verification boundary

For a selected root-correct repair, passing tests should be capable of falsifying the selected method rather than merely showing new code executes. Where material, include original-defect reproduction, repaired behavior, same-root/future-drift coverage, boundary/bypass discrimination, directly affected regressions, real consumer integration, and exact-target/exact-Head verification.

A proposed test is not executed evidence. A conformance check is insufficient when a materially different nonconforming/surface repair could pass the same check without an observable distinction.

Keep lifecycle stages separate in reporting:

`implementation ≠ selected-method conformance ≠ focused tests ≠ regression tests ≠ exact-Head CI ≠ fresh rereview ≠ merge/release/Owner authorization`

One stage does not imply the next.

## Definition of Done for Foundation changes

A Foundation/document-governance change is structurally complete when:

- the canonical verifier passes on the exact candidate;
- internal links are valid;
- machine-readable artifacts parse;
- changed canonical semantics have been reflected in relevant evaluation scenarios/rubric or a reason is documented for no fixture change;
- every material evaluator criterion remains derivable from canonical guidance plus scenario input;
- reviewer/evaluator separation remains intact;
- agent instructions remain concise pointers rather than duplicated manuals;
- claims stay within the verification boundary.
