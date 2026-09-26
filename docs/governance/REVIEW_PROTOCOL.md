# Deep Engineering Review Protocol

## Goal

Use the model's existing engineering knowledge in a disciplined, context-sensitive sequence.

This protocol is not a universal checklist. Steps may stay compact when they are not decision-material, but no material finding should skip the authority/evidence boundary.

## 0. Scope

Classify the review:

- `PR_SCOPE` — changed/new decisions are primary; expand context only as needed.
- `REPOSITORY_SCOPE` — system-wide architecture/evolution is primary.

## 1. Build the intent model

Before rationalizing local implementation, extract:

- purpose;
- success conditions;
- invariants;
- accepted architecture decisions;
- explicit compatibility/support boundaries;
- unacceptable outcomes;
- known owner decisions.

Record `UNSTATED` rather than inventing intent.

## 2. Build the reality model

Inspect enough target evidence to identify:

- material entities/dependencies;
- ownership and lifecycle;
- public/internal contract boundaries;
- failure/change model;
- state/data flow;
- relevant history where needed.

Unknowns remain unknown.

## 3. Derive scenarios, obligations, and capabilities

For each material entity property:

`property → scenario → structural obligation → required capability`

Only derive obligations that can materially change engineering judgment.

When evidence supports a capability-shape issue, use the canonical [`MISSING_CAPABILITY`, `MISFIT_CAPABILITY`, or `EXCESS_CAPABILITY`](../core/REASONING_MODEL.md#capability-finding-classes) semantics. Do not force a capability class when the conclusion has another shape.

## 4. Extract material engineering decisions

List the decisions that implement or constrain those capabilities.

Do not confuse declarative requirement text with proof the implementation satisfies it.

## 5. Route reasoning methods

Select the smallest set of reasoning/investigation methods likely to change the review outcome.

Possible families include:

- contract/boundary analysis;
- lifecycle/evolution analysis;
- change-impact/history analysis;
- concurrency/state analysis;
- failure/recovery analysis;
- algorithm/data-structure fit;
- performance/profiling;
- security/threat analysis;
- ownership/responsibility analysis;
- counterfactual redesign;
- sensitivity/tradeoff analysis;
- architecture comparison.

The model may activate methods not named here when the situation warrants them.

## 6. Track method coverage

For every materially activated method, initialize and maintain the canonical [Method Coverage Ledger](../core/REASONING_MODEL.md#method-coverage-ledger).

Update each entry from actual execution evidence. A method that ran and found nothing material must remain distinguishable from one that never ran or was blocked. Do not add never-activated methods merely to make the ledger look complete.

## 7. Challenge constraints and decisions

For each suspicious material decision, ask:

- Why does this constraint exist?
- Is it intrinsic to the problem or created by the implementation?
- What changes if the underlying dependency/assumption changes?
- Is the decision attached to a stable sufficient contract or a volatile implementation detail?
- Does the selected structure fit the actual access/change/failure pattern?
- If designing from the same intent and reality today, would this decision still be selected?

## 8. Adapt after material evidence

Apply the canonical [adaptation / re-routing checkpoint](../core/REASONING_MODEL.md#adaptation--re-routing-checkpoint) whenever a material reasoning result or new evidence appears during the remainder of the review.

If the evidence changes the working system model, obligation/hypothesis/root cause, abstraction level, tradeoff/alternatives, required evidence, or method selection:

`update model → re-evaluate routing → activate only the smallest newly relevant method set → retire no-longer-material methods → continue`

Keep the Method Coverage Ledger consistent with the reroute. Do not restart the whole review or rerun all methods merely because one fact changed.

## 9. Find sensitivity/tradeoff points

Identify disproportionate change propagation and quality tradeoffs.

A fail-closed mechanism may improve correctness/safety while damaging evolvability; both belong in the review.

## 10. Use temporal evidence only when useful

Inspect history, co-change, prior incidents, or previous fixes when it can discriminate between competing explanations.

Do not mine history ceremonially.

## 11. Synthesize findings into root causes/risk themes

Prefer:

`several symptoms → one evidenced mechanism`

over a flat list of local complaints.

## 12. Search same-level alternatives

Do not answer an architecture problem with a micro-optimization and call it solved.

Compare materially distinct repair families at the abstraction level of the root cause.

## 13. Evaluate depth, blast radius, and adoption cost

For the leading improvement:

- confirm the causal chain reaches intent/system reality/external constraint;
- map affected consumers and boundaries;
- separate technical superiority from migration/adoption cost;
- escalate owner-dependent business/risk acceptance decisions instead of inventing them.

## 14. Qualify

Each material conclusion should use one qualification state:

- `CONFIRMED_FINDING`
- `JUSTIFIED_DEVIATION`
- `NOT_PROVEN`
- `NO_MATERIAL_ISSUE`

When the conclusion is specifically a capability-shape issue, record the applicable capability class separately. Capability class and qualification state are complementary; neither replaces the other.

Avoid certainty inflation.

## 15. Stop at sufficiency

Stop when additional review is unlikely to change:

- a material finding;
- the leading root cause;
- the preferred repair family;
- blast radius;
- required owner input;
- or the exact next action.

## Recommended review output

Keep output compact but auditable:

```text
Scope:
Intent / governing constraints:
Material system inventory:
Derived obligations:
Material engineering decisions:
Method Coverage Ledger:
Findings:
Risk themes:
Alternatives considered:
Blast radius / adoption cost:
Unverified areas:
Recommended next engineering action:
Stop reason:
```

Do not expose private chain-of-thought. Report conclusions, evidence, derivations, and concise rationale.
