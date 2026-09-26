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

## 6. Challenge constraints and decisions

For each suspicious material decision, ask:

- Why does this constraint exist?
- Is it intrinsic to the problem or created by the implementation?
- What changes if the underlying dependency/assumption changes?
- Is the decision attached to a stable sufficient contract or a volatile implementation detail?
- Does the selected structure fit the actual access/change/failure pattern?
- If designing from the same intent and reality today, would this decision still be selected?

## 7. Find sensitivity/tradeoff points

Identify disproportionate change propagation and quality tradeoffs.

A fail-closed mechanism may improve correctness/safety while damaging evolvability; both belong in the review.

## 8. Use temporal evidence only when useful

Inspect history, co-change, prior incidents, or previous fixes when it can discriminate between competing explanations.

Do not mine history ceremonially.

## 9. Synthesize findings into root causes/risk themes

Prefer:

`several symptoms → one evidenced mechanism`

over a flat list of local complaints.

## 10. Search same-level alternatives

Do not answer an architecture problem with a micro-optimization and call it solved.

Compare materially distinct repair families at the abstraction level of the root cause.

## 11. Evaluate depth, blast radius, and adoption cost

For the leading improvement:

- confirm the causal chain reaches intent/system reality/external constraint;
- map affected consumers and boundaries;
- separate technical superiority from migration/adoption cost;
- escalate owner-dependent business/risk acceptance decisions instead of inventing them.

## 12. Qualify

Each material conclusion should be one of:

- `CONFIRMED_FINDING`
- `JUSTIFIED_DEVIATION`
- `NOT_PROVEN`
- `NO_MATERIAL_ISSUE`

Avoid certainty inflation.

## 13. Stop at sufficiency

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
Activated reasoning methods:
Findings:
Risk themes:
Alternatives considered:
Blast radius / adoption cost:
Unverified areas:
Recommended next engineering action:
Stop reason:
```

Do not expose private chain-of-thought. Report conclusions, evidence, derivations, and concise rationale.
