# Canonical Reasoning Model

## Core idea

Engineering Compass is a **reasoning-strategy orchestrator**.

It does not say “always run these 40 checks.” It characterizes the situation and activates the engineering methods that can materially change the review outcome.

Canonical loop:

`Characterize → Select methods → Sequence → Observe evidence → Adapt → Evaluate → Stop`

## System-to-review graph

```text
Intent / Authority
        ↓
System Inventory
        ↓
Material Properties
        ↓
Change / Failure Scenarios
        ↓
Structural Obligations
        ↓
Required Capabilities
        ↓
Material Engineering Decisions
        ↓
Reasoning-Strategy Selection
        ↓
Sensitivity / Tradeoff Analysis
        ↓
Temporal Evidence when material
        ↓
Root Causes + Risk Themes
        ↓
Same-Abstraction-Level Alternatives
        ↓
Depth + Blast Radius + Cost/Benefit
        ↓
Smallest Root-Correct Improvement
```

The structure is a graph, not a strict tree: one entity may create several obligations and one capability may satisfy obligations from several entities.

## 1. Intent / authority

Establish the highest-level purpose, invariants, constraints, unacceptable outcomes, and already accepted decisions before allowing local implementation to justify itself.

Do not infer project requirements from implementation merely because the implementation exists.

A lower-level implementation plan cannot silently override a conflicting higher-level product or architecture objective.

## 2. System inventory

Identify only entities that materially shape the reviewed capability, for example:

- host platforms;
- frameworks/plugins/libraries;
- services/APIs;
- databases/storage;
- queues/caches;
- browsers/runtimes;
- build/release systems;
- external protocols or schemas.

For each material entity, inspect relevant characteristics such as:

- ownership/control;
- lifecycle and versioning;
- independent change;
- contract stability;
- mutability;
- latency/failure modes;
- concurrency;
- scale;
- persistence;
- trust/security boundary.

Do not propagate every property. A property enters the graph only when ignoring it could materially affect correctness, reliability, maintainability, security, evolution, operability, or another stated objective.

## 3. Material scenario layer

Convert a relevant property into a concrete change/failure scenario before deriving an obligation.

Example:

```text
Entity: external versioned dependency
Property: updates independently
Scenario: upstream version changes while our integration remains deployed
Expected response: integration determines whether its required contract still holds
```

Scenarios make architectural claims testable and reduce vague “best practice” reasoning.

## 4. Structural obligations

Some system facts create obligations even when the project documents do not explicitly state them.

Example:

```text
Fact: capability depends on an externally controlled, independently versioned host.
Therefore: the capability needs a defined strategy for relevant upstream evolution.
```

This does **not** imply “support every version.” It implies that upstream evolution cannot remain an undefined architectural state.

Structural obligations must be evidence-backed derivations, not invented owner requirements.

## 5. Engineering presumptions

General engineering knowledge may create a **rebuttable presumption**, not a binding project requirement.

Examples:

- depend on the most stable sufficient contract;
- avoid accidental constraints narrower than the real dependency;
- make expected change reasonably affordable;
- do not pay recurring complexity without a concrete failure avoided.

Use:

`Presumption → Challenge → Search for defeater`

A valid project or technical reason may justify deviation.

## 6. Required capabilities

Translate obligations into capabilities before judging mechanisms.

Examples:

- upstream evolution → compatibility strategy;
- shared mutable state → concurrency/consistency strategy;
- network dependency → timeout/failure/retry/idempotency strategy as applicable;
- persistent schema → migration/evolution strategy.

A missing capability and a poorly implemented capability are different findings.

## 7. Material engineering decisions

Extract decisions from the target before applying deep-review lenses.

Examples:

- use a private seam;
- pin an exact host build;
- fail closed for unknown hosts;
- duplicate state;
- add a cache;
- use a queue;
- retry a side effect.

Review decisions, their assumptions, and their consequences—not only syntax.

## 8. Reasoning-strategy selection

Choose methods because the situation triggers them.

Illustrative routing:

| Situation signal | Candidate reasoning methods |
|---|---|
| externally evolving dependency | lifecycle, compatibility, contract/boundary analysis |
| private/internal seam | boundary leakage, stability, alternative seam analysis |
| shared persistent state | concurrency, consistency, ownership, recovery analysis |
| network/service dependency | partial-failure, latency, timeout, retry/idempotency analysis |
| repeated cross-file change | change-propagation/history/co-change analysis |
| exact constraints/pinning | necessity-of-constraint, counterfactual, compatibility analysis |
| new abstraction/control | minimum-complexity, failure-prevented, maintenance-cost analysis |
| competing architecture methods | same-level comparison, tradeoff and robustness analysis |

This table is routing guidance, not a closed checklist.

The model may use other engineering methods it already knows when evidence shows they are more appropriate.

## 9. Sensitivity and tradeoff points

Look for decisions where a small input/upstream/parameter change produces a disproportionate system effect.

Also identify decisions that materially improve one quality while degrading another.

Do not optimize one quality in isolation.

## 10. Temporal evidence

Use version history, recurring incidents, co-change, migrations, and previous fixes when they can distinguish between hypotheses.

History is evidence, not destiny. A repeated pattern may reveal a hotspot; it does not automatically prove root cause.

## 11. Root causes and risk themes

Do not leave several local symptoms as unrelated findings when they share one architectural cause.

Synthesize a risk theme when evidence supports a common mechanism.

Example:

```text
internal seam
+ exact-version admission
+ exact-file fingerprints
+ unrelated upstream changes causing rejection
→ Upstream Implementation Coupling
```

## 12. Same-abstraction-level alternatives

A proposed repair must address the problem at the same or higher causal level.

If the problem is architecture coupling, caching a repeated hash may be a valid micro-optimization but it is not an architecture alternative.

Before choosing a repair:

1. identify the finding's abstraction level;
2. search for materially different alternatives at that level;
3. eliminate candidates that violate hard constraints;
4. compare surviving tradeoffs;
5. keep local optimizations separate from root-cause repairs.

## 13. Depth sufficiency

Ask “why does this decision exist?” until reaching one of:

- authoritative intent;
- an inspected external constraint;
- a stable system property;
- an evidence-backed unavoidable tradeoff.

If the chain ends only in the current implementation, the explanation is circular.

Do not recurse indefinitely. Stop when deeper analysis cannot materially change the decision.

## 14. Blast radius and cost/benefit

For a root-correct alternative, determine:

- branch-local;
- module-local;
- repository-wide;
- cross-system/cross-repository.

Map actual dependencies before claiming scope.

A more fundamental solution may be technically better yet economically unjustified. Keep technical depth and adoption cost as separate questions.

## 15. Smallest root-correct improvement

Prefer the smallest coherent change that:

- removes or properly contains the deepest material cause;
- preserves valid requirements and behavior;
- does not create greater lifecycle/maintenance cost;
- can be verified at the level of the claim.

Do not reward complexity merely because it looks more architectural.

## Review failure classes

The model should distinguish at least:

- `MISSING_CAPABILITY` — an obligation exists but no handling strategy exists;
- `MISFIT_CAPABILITY` — handling exists but is poorly matched to the real obligation;
- `EXCESS_CAPABILITY` — material complexity exists without a demonstrated obligation/failure;
- `JUSTIFIED_DEVIATION` — the implementation departs from a normal engineering presumption for an evidence-backed reason;
- `NOT_PROVEN` — evidence is insufficient to decide.

## Stop rule

Additional reasoning is justified only if it can plausibly:

- reveal a material obligation/failure;
- change a finding's confidence or classification;
- change the leading repair family;
- expose a larger blast radius or tradeoff;
- invalidate an assumption;
- change the exact next engineering action.

Otherwise, stop.
