# Agent Entrypoint — Engineering Compass

Repository phase: `BASELINE_COMPLETE`

Acceptance boundary: accepted Current authority comes from `main`. Candidate branches are review material, not accepted authority merely because files exist. The historical initial-Foundation baseline remains recorded in `repository.manifest.json`.

## Purpose

Use this repository to govern **how engineering expertise is applied and safely operationalized**, not to re-teach engineering knowledge.

## Selective read order

Do not dump the repository into context.

1. `repository.manifest.json`
2. `docs/core/MISSION.md`
3. `docs/core/REASONING_MODEL.md`
4. `docs/governance/AUTHORITY.md`
5. `docs/governance/REVIEW_PROTOCOL.md`
6. For executable review/control work: `docs/runtime/ARCHITECTURE.md`
7. If repair is possible: `docs/runtime/ROOT_CAUSE_REPAIR.md` and `docs/runtime/ACTION_MODEL.md`
8. If an action prompt is required: `docs/runtime/PROMPT_PIPELINE.md`
9. `docs/runtime/LLM_ASSESSMENT_CONTRACT.md` when producing/validating structured assessment
10. `docs/research/RESEARCH_BASIS.md` only when rationale/research provenance matters
11. fixtures only for regression/evaluation work
12. `docs/governance/VERIFICATION.md` when changing the repository or qualifying execution claims

## Operating rules

- Start from target purpose and authority before rationalizing implementation details.
- Separate caller intent, verified facts, reviewer judgment, root-cause repair design, action projection, prompt generation, implementation, validation, and completion.
- Build a bounded system inventory before selecting review methods.
- Derive only material scenarios/obligations.
- Extract material engineering decisions; do not reduce review to changed lines.
- Select and sequence reasoning methods based on the situation; do not run a flat universal checklist.
- Maintain the Method Coverage Ledger for materially activated methods.
- After material evidence, re-evaluate the working model and routing rather than restarting everything.
- Match problem and repair at the same abstraction level.
- Prefer the smallest root-correct improvement; deeper is not automatically better.
- Claim strength must not exceed evidence.
- Stop when more analysis is unlikely to change the material decision.

## Executable review boundary

When using the Python runtime:

1. caller supplies only target selectors + review intent;
2. `collect` resolves target facts/evidence;
3. the model supplies a structured assessment bound to that exact evidence identity;
4. `project` validates the assessment and emits one canonical next action;
5. no implementation prompt is permitted until root cause, method selection, Conformance Lock, and falsification obligations are complete;
6. when a prompt is required, use the Prompt-Pipeline handoff/compile path rather than inventing a parallel renderer.

Prompt-Pipeline is an external SSOT. A locked checkout mismatch is a blocker, not permission to reconstruct its behavior from memory.

## Instruction / enforcement boundary

Canonical docs provide reasoning authority and prompt-level influence. The Python runtime mechanically enforces only its explicit contracts/transitions. It does not mechanically prove semantic engineering correctness.

Run repository verification before claiming runtime/repository PASS:

```bash
python3 scripts/verify_repo.py
python3 -m unittest discover -s tests -p 'test_*.py'
```
