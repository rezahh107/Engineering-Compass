# Agent Entrypoint — Engineering Compass

Repository phase: `BASELINE_COMPLETE`

Acceptance boundary: the initial Foundation baseline has been human-approved and merged to `main`; its historical commit/tree identity is recorded in `repository.manifest.json`. Accepted Current authority comes from `main`. A candidate branch is review material, not accepted authority merely because the files exist.

## Purpose

Use this repository to govern **how engineering expertise is applied**, not to re-teach engineering knowledge.

## Selective read order

Do not dump the repository into context.

1. `repository.manifest.json`
2. `docs/core/MISSION.md`
3. `docs/core/REASONING_MODEL.md`
4. `docs/governance/AUTHORITY.md`
5. `docs/governance/REVIEW_PROTOCOL.md` for an actual review
6. `docs/research/RESEARCH_BASIS.md` only when rationale/research provenance matters
7. a fixture under `fixtures/` only when regression/evaluation work requires it
8. `docs/governance/VERIFICATION.md` when making or qualifying repository changes

## Operating rules

- Start from the target system's purpose and authority before rationalizing implementation details.
- Separate explicit requirements, evidence-backed derivations, structural obligations, rebuttable engineering presumptions, and hypotheses.
- Build a bounded system inventory before selecting review methods.
- Derive only **material** scenarios/obligations; do not propagate every property of every dependency.
- Extract material engineering decisions; do not reduce review to changed lines.
- Select and sequence reasoning methods based on the situation. Do not run a flat universal checklist.
- Track materially activated methods with the compact Method Coverage Ledger so applied findings, applied no-findings, non-execution, and blockers remain visible without exposing private chain-of-thought.
- After material new evidence, re-evaluate the working model and method routing; activate only the smallest newly relevant method set rather than restarting the whole review.
- A problem and its proposed solution must be compared at the same abstraction level.
- Prefer the smallest root-correct improvement; deeper is not automatically better.
- Treat complexity, controls, evidence requests, and additional analysis as costs that require a named failure or decision value.
- Claim strength must not exceed evidence.
- Stop when more analysis is unlikely to change the engineering decision.

## Instruction / enforcement boundary

These files provide `prompt_level_influence`. They do not mechanically enforce model reasoning.

Executed repository checks, when present, prove only what they actually exercise. See `docs/governance/VERIFICATION.md`.
