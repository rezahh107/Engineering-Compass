# Repository Verification Contract

## Canonical commands

```bash
python3 scripts/verify_repo.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

Humans, agents, and CI should use these same underlying contracts.

## What the repository verifier checks

The canonical verifier checks:

- required Foundation + runtime files exist;
- `repository.manifest.json` is valid and lifecycle metadata is consistent;
- canonical manifest surfaces resolve;
- machine-readable schemas, fixtures, and integration lock are valid JSON;
- Prompt-Pipeline lock identity is SHA-shaped and declares the current inspected integration boundary;
- semantic regression fixture retains its non-canonical test-spec authority;
- executable runtime fixtures can be validated and produce the expected guarded actions;
- local Markdown links resolve;
- agent instructions reference the canonical verification commands.

## What unit tests check

The runtime unit suite exercises deterministic transition invariants, including:

- caller intent cannot inject authoritative target facts;
- a confirmed Finding without a confirmed root cause cannot route to code modification;
- materially competing methods force FULL comparison semantics;
- pseudo-alternatives with the same decision signature are rejected;
- numeric scoring/weights are rejected;
- equivalent finalists can route to owner decision instead of a fabricated winner;
- implementation handoff binds root cause, selected method, Conformance Lock, falsification obligations, and selected-method infeasibility behavior;
- no prompt is produced when the canonical action does not require one;
- repository-scope inventory cannot masquerade as semantic source coverage, and exact-blob source limits fail closed;
- exact-blob changes alter evidence identity and stale prior assessments;
- Commit statuses stay distinct from Check Runs, including proven-empty status lists;
- authoritative review-thread resolution/outdated state is independently collected and pagination/auth failures block PR full coverage.

## Cross-repository Prompt-Pipeline check

CI separately checks out the Prompt-Pipeline commit recorded in `integrations/prompt-pipeline.lock.json` and runs the Engineering Compass lock verifier against the actual external Git tree.

When the integration smoke job executes, Engineering Compass builds canonical Prompt-Pipeline intake and invokes Prompt-Pipeline through its `--request` path. A generated artifact keeps the authority state reported by Prompt-Pipeline; generation is not auto-approval.

## What PASS does not prove

A repository/runtime PASS does **not** prove:

- an LLM will discover every material system property;
- a structured root-cause statement is objectively correct merely because its contract validates;
- the selected repair method is globally optimal;
- a generated Prompt-Pipeline artifact was owner-approved unless that external state is actually observed;
- an implementation was performed;
- proposed tests or CI passed unless actually executed and inspected;
- a fresh exact-Head engineering rereview has completed;
- merge/deploy authorization exists.

## Semantic regression boundary

`fixtures/gravity-flow-version-coupling.json` remains a `NON_CANONICAL_TEST_SPEC` for LLM semantic behavior. Runtime fixtures are executable **control-plane** tests; they do not convert the semantic fixture into a model-evaluation harness.

Report model semantic regression as `NOT_EXECUTED` unless a real model evaluation was performed.

## Exact-target qualification

For a repository change:

1. run the canonical verifier and unit tests on the exact resulting tree/Head;
2. inspect CI for the same Head when relevant;
3. distinguish local runtime tests, external Prompt-Pipeline lock checks, Prompt-Pipeline generation state, target implementation tests, and fresh rereview;
4. do not call skipped/unavailable stages PASS.

## Definition of Done for runtime changes

A runtime/governance change is structurally complete when:

- canonical verifier passes;
- runtime unit tests pass;
- machine-readable contracts remain valid;
- changed transitions have focused regression fixtures/tests;
- Prompt-Pipeline lock drift is absent or deliberately reconciled from an inspected source;
- claims stay within the stage actually verified.
