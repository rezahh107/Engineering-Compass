# Agent Entrypoint — Engineering Compass

Repository phase: `BASELINE_COMPLETE`

Acceptance boundary: the initial Foundation baseline has been human-approved and merged to `main`; its historical commit/tree identity is recorded in `repository.manifest.json`. Accepted Current authority comes from `main`. A candidate branch is review material, not accepted authority merely because the files exist.

## Purpose

Engineering Compass is primarily an **LLM-native reasoning-governance repository**. Its normal consumption path is:

`LLM reads the smallest relevant guidance → understands the governing reasoning system → applies it during engineering review`

Use this repository to govern **how engineering expertise is applied**, not to re-teach engineering knowledge and not to create a parallel execution/control subsystem unless a real machine-executed consumer requires one.

## Selective read order

Do not dump the repository into context.

1. `repository.manifest.json`
2. `docs/core/MISSION.md`
3. `docs/core/REASONING_MODEL.md`
4. `docs/governance/AUTHORITY.md`
5. `docs/governance/REVIEW_PROTOCOL.md` for an actual review
6. `docs/research/RESEARCH_BASIS.md` only when rationale/research provenance matters
7. a scenario fixture under `fixtures/` only when regression/evaluation work requires it
8. `docs/governance/VERIFICATION.md` when making or qualifying repository changes
9. `fixtures/semantic-evaluation-rubric.json` only for evaluator-side semantic evaluation; never include it in clean reviewer-model input

## Operating rules

- Start from the target system's purpose and authority before rationalizing implementation details.
- Separate explicit requirements, evidence-backed derivations, structural obligations, rebuttable engineering presumptions, and hypotheses.
- Build a bounded system inventory before selecting review methods.
- Derive only **material** scenarios/obligations; do not propagate every property of every dependency.
- Extract material engineering decisions; do not reduce review to changed lines.
- Select and sequence reasoning methods based on the situation. Do not run a flat universal checklist.
- Track materially activated methods with the compact Method Coverage Ledger so applied findings, applied no-findings, non-execution, and blockers remain visible without exposing private chain-of-thought.
- After material new evidence, re-evaluate the working model and method routing; activate only the smallest newly relevant method set rather than restarting the whole review.
- A confirmed symptom is not a confirmed root cause. Do not move directly from a Finding to implementation while the causal mechanism or correct enforcement boundary remains unresolved.
- When useful, apply the surface-patch counterfactual: if this manifestation disappeared but the same cause appeared at another reachable instance, would the proposed repair still prevent or expose the defect?
- A problem and its proposed solution must be compared at the same abstraction level.
- Prefer the smallest root-correct improvement; deeper is not automatically better.
- Treat complexity, controls, evidence requests, and additional analysis as costs that require a named failure or decision value.
- Claim strength must not exceed evidence.
- Stop when more analysis is unlikely to change the engineering decision.

## Guidance / validation / proof boundary

Keep three levels distinct:

- **Guidance** — repository-visible instructions or artifacts that can influence an LLM. Existence does not prove execution or compliance.
- **Validation** — a deterministic or model-mediated check that, when actually run, establishes only its explicit predicates. A validator PASS does not prove semantic engineering correctness.
- **Proof of mechanical control** — evidence that an externally forced path actually executed a non-bypassable control for the exact claimed predicate. Model-mediated invocation is not such a path when the model can skip it.

For any claimed control, identify the failure it prevents, any exact machine-checkable predicate, the executor, the consumer, and the bypass possibility. If no externally forced consumer exists, do not describe repository code, schemas, contracts, or instructions as mechanical enforcement.

## Instruction / enforcement boundary

These files provide `prompt_level_influence`. They do not mechanically enforce model reasoning.

Executed repository checks, when present, prove only what they actually exercise. Semantic quality requires behavior-level evaluation with scenario input separated from evaluator expectations. See `docs/governance/VERIFICATION.md`.
