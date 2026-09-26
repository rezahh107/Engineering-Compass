# ADR-0001 — Reasoning Orchestration Instead of an Engineering Checklist

- Status: Accepted; repository authority was established by the human-approved merge of PR #1 to `main`.
- Decision scope: Engineering Compass core architecture.

## Context

LLMs already contain broad software-engineering knowledge and know many methods for analyzing code and architecture.

The recurring failure is not simply lack of knowledge. It is inconsistent activation and sequencing of that knowledge:

- a model may optimize a local implementation before questioning why the implementation strategy exists;
- it may inspect changed lines without reconstructing system intent or dependency lifecycle;
- it may choose one familiar review lens and omit another that is more discriminating;
- it may continue analysis after the decision is already sufficient;
- or it may run a large generic checklist that dilutes attention.

## Decision

Engineering Compass will be a **reasoning-strategy orchestrator**, not an encyclopedic engineering knowledge base.

The core will focus on:

1. situation characterization;
2. system inventory and material properties;
3. scenario/obligation/capability derivation;
4. material decision extraction;
5. reasoning-method selection and sequencing;
6. evidence-driven adaptation;
7. root-cause/risk-theme synthesis;
8. same-level alternative comparison;
9. depth/blast-radius/cost analysis;
10. stop-at-sufficiency behavior.

## Consequences

### Positive

- preserves the model's broad engineering knowledge instead of duplicating it;
- keeps the repository lighter and more general across languages/frameworks;
- makes review coverage and strategy use more auditable;
- encourages system-level reasoning without forcing maximal architecture;
- reduces overlap with CI/static-analysis tooling.

### Costs / risks

- prompt guidance cannot mechanically guarantee reasoning behavior;
- regression evaluation needs semantic fixtures and eventually a model-evaluation harness;
- routing rules must remain generative enough not to become a hidden checklist;
- system characterization quality becomes a key dependency.

## Guard

Do not add a permanent rule or category merely because a known bug class exists.

Add permanent orchestration structure only when it improves how the model selects/applies engineering reasoning across a meaningful class of situations.
