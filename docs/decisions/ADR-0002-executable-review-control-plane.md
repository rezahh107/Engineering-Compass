# ADR-0002 — Executable Review Control Plane

Status: Accepted candidate for review

## Context

The initial Foundation established Engineering Compass as a reasoning-strategy orchestrator, but Markdown guidance alone could not guarantee target identity, stage separation, root-cause repair admission, action routing, or Prompt-Pipeline compatibility.

The project must preserve a critical boundary: the LLM performs engineering judgment; deterministic code must not pretend to discover architecture truth by replacing that judgment with a static checklist.

## Decision

Introduce a small standard-library Python control plane that:

1. supports `PR_SCOPE`, `REF_DELTA_SCOPE`, and `REPOSITORY_SCOPE` target selectors;
2. collects read-only GitHub evidence and resolves exact target identity;
3. validates model-produced assessment against evidence references and target binding;
4. forbids direct Finding→Implementation Prompt transitions;
5. validates root-cause anchors, BOUNDED/FULL repair routing, materially distinct methods, ordered comparison, Conformance Lock, and falsification obligations;
6. projects one canonical next action;
7. integrates with Prompt-Pipeline through an inspected external compatibility lock and canonical `--request` path;
8. never auto-approves Prompt-Pipeline artifacts or performs merge/deploy/write actions.

## Consequences

Positive:

- review stages become auditable and reproducible;
- stale or incomplete evidence can fail closed without erasing valid judgment;
- symptom patches cannot become implementation prompts merely because a Finding exists;
- Prompt-Pipeline remains an external SSOT rather than copied policy;
- branch and repository review can share one target abstraction with PR review.

Costs:

- assessment JSON has a real contract;
- Prompt-Pipeline lock upgrades require deliberate reinspection;
- semantic engineering quality still requires an LLM/human and cannot be inferred from runtime PASS.

## Rejected alternatives

- deterministic checklist as the primary reviewer — rejects the repository mission;
- copy Prompt-Pipeline templates/rules into Engineering Compass — creates drift and parallel authority;
- directly reuse the historical PR-Inspector action renderer — Prompt-Pipeline marks that consumer path retired/fail-closed;
- allow implementation agents to reinterpret the selected method — breaks the repair-selection boundary.
