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
Scenario-Driven Gap Discovery (when material)
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

## Scenario-Driven Gap Discovery

Use **Scenario-Driven Gap Discovery** after enough Intent / Authority and inspected Reality are known to construct a useful operational model, but before structural obligations, root-cause framing, material engineering decisions, or repair direction are finalized.

It is a bounded reasoning strategy, not a separate runtime, workflow engine, control plane, second review pipeline, mandatory universal checklist, or exhaustive model-checking exercise. Activate it only when it can plausibly reveal a material missing state, interaction, assumption, failure path, drift, or decision.

A discovery may require the reviewer to revise the operational model, assumptions, structural obligations, root-cause framing, evidence needs, or reasoning-method routing. Feed the result back into the main review graph rather than maintaining a parallel analysis track.

### Scope adaptation

For `REPOSITORY_SCOPE`, model the material operational system broadly enough to expose repository-level blind spots.

For `PR_SCOPE`, identify the behavioral blast radius of the change and exercise only affected material states, transitions, invariants, dependencies, progress obligations, and interactions by default.

Do not simulate the entire repository for a trivial or unrelated change.

### Operational model discovery

When material, identify:

- actors and permission/authority boundaries;
- material states and state ownership;
- transitions, guards, preconditions, and postconditions;
- persistent sources of truth versus derived/display state;
- external dependencies and host/platform capabilities;
- navigation and lifecycle boundaries;
- concurrency and multi-actor interaction points;
- environment dimensions that can change behavior;
- assumptions whose falsity would materially change the result.

Explicitly challenge whether an important state, actor, dependency, transition, or environment dimension is missing from the model itself. A model that cleanly exercises only the states it already knows is not evidence that the model is complete.

### Invariants and progress obligations

Derive both when applicable:

- **invariants / safety properties** — what must never become false;
- **progress / liveness obligations** — what valid outcomes must remain achievable.

A system that preserves every safety invariant but can become permanently stuck must not automatically be treated as correct.

These concepts do not require formal specification machinery. Use the smallest notation that makes the material obligation clear.

### Scenario expansion

Select only scenario families material to the target. Candidate families include:

- normal completion;
- validation / partial completion;
- explicit technical failure;
- ambiguous outcome / unknown commit state;
- stale state / reload / back-forward;
- concurrency, retries, duplicate actions, reordered events;
- permission / role / session changes;
- dependency timeout, unavailability, version or capability drift, fallback;
- malformed / empty / boundary / real-world data shapes;
- responsive, zoom, accessibility, input-mode, RTL/BiDi when user-facing;
- migration, upgrade, rollback, old persisted state, or platform drift when material.

Structured scenario notation may be used when useful, but must not become ceremony.

### Interaction-failure reasoning

Do not stop at broken individual components.

Challenge whether individually correct components, layers, or controls can combine into an incorrect system result because ownership, ordering, timing, coordination, or assumptions are wrong.

### Bounded combinatorial exploration

Do not enumerate Cartesian products.

Use pairwise or higher-order/t-way reasoning only where the interacting dimensions are materially relevant, plus known high-risk scenarios. Prefer the smallest combinations capable of changing the engineering decision.

Never claim complete real-world coverage merely because the known model received combinatorial coverage.

### Drift / conformance

Compare the material destination and reality across relevant surfaces such as:

- current Owner/project authority;
- accepted architecture/product contracts;
- documentation;
- tests and fixtures;
- implementation/configuration;
- actual runtime evidence when available.

A difference is not automatically a defect. Distinguish:

- justified deviation;
- retained future capability;
- obsolete contract/test;
- actual drift.

### Gap disposition

Every material discovered gap should end in one useful disposition:

- `AUTO_RESOLVE_WITHIN_AUTHORITY`
- `TECHNICAL_QUALIFICATION_REQUIRED`
- `OWNER_ESCALATION_REQUIRED`
- `NO_MATERIAL_ISSUE_OR_JUSTIFIED_DEVIATION`

Authority comes before reversibility.

Do not burden the Owner with standard low-risk reversible engineering defaults when existing authority and evidence are enough. Escalate only when Owner authority is genuinely required, including materially different product/business meaning, user rights, policy, data ownership/retention, workflow semantics, external commitments, or another durable/high-cost decision.

### Evidence boundary

Simulation is reasoning, not runtime proof.

When a scenario depends on an unverified runtime, host, provider, or capability fact, keep the conclusion `NOT_PROVEN` or route it to `TECHNICAL_QUALIFICATION_REQUIRED`. Do not turn a simulated outcome into an observed fact.

### Two-key stop rule

Stop Scenario-Driven Gap Discovery only when both are sufficiently true for the materiality of the target:

**A. Structural sufficiency for the known model**

Relevant states/transitions, invariants, progress obligations, scenario families/interactions, and discovered-gap dispositions are adequately covered.

**B. Discovery/materiality sufficiency**

Further exploration is no longer reasonably likely to reveal a new material state, dependency, invariant/progress obligation, interaction failure, drift, failure family, Owner decision, repair-family change, or materially larger blast radius.

Do not chase ceremonial completeness after both conditions are satisfied.

### Repair and regression feedback

Do not jump from a simulated symptom directly to a patch.

Feed discoveries back into the problem model, evidence request, structural obligations, and root-cause analysis. Keep the existing North Star: the smallest root-correct improvement with bounded blast radius and durable cost.

After implementation, re-exercise the affected operational model and relevant interactions. Reuse the prior model and broaden it only when new evidence requires it.

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

### Capability finding classes

These classes describe the **shape of an evidenced capability issue**. They are not mandatory outcomes and must not be assigned merely to make a review fit a taxonomy.

#### `MISSING_CAPABILITY`

```text
material obligation exists
→ required capability is absent
```

Example shape: an external network dependency materially permits timeout/failure, but no applicable failure-handling strategy exists.

#### `MISFIT_CAPABILITY`

```text
material obligation exists
→ capability exists
→ chosen strategy/mechanism does not adequately fit the real system property
```

Example shape: compatibility management exists, but exact implementation identity is used where evidence shows a demonstrably sufficient stable behavioral/public contract is available.

Do not label a capability `MISFIT_CAPABILITY` merely because another design looks cleaner or more elegant. The mismatch requires evidence.

#### `EXCESS_CAPABILITY`

```text
no material obligation or named failure justifies the mechanism
→ material complexity/control/capability nevertheless exists
```

This class captures overengineering only when the missing justification is itself evidenced; it is not a shortcut for disliking complexity.

No capability finding should be created unless the evidence supports it.

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

### Method Coverage Ledger

Track only reasoning methods that were materially activated by routing. The ledger exists to distinguish “examined and no material issue found” from “not examined”; it is not an inventory of every method the model knows.

For each activated method, record only auditable execution information:

```text
method:
trigger:
status:
evidence:
outcome:
```

Supported statuses:

- `APPLIED_FINDING` — the method ran and produced a material finding/result;
- `APPLIED_NO_FINDING` — the method ran and found no material issue;
- `NOT_EXECUTED` — the method was activated but did not run;
- `BLOCKED` — the method could not be executed because required evidence/access was unavailable.

If later evidence materially reroutes the review and an activated-but-unrun method is no longer decision-material, keep it visible as `NOT_EXECUTED` and state in `outcome` that it was retired by rerouting. Do not invent a finding merely to close the entry.

The ledger reports conclusions, evidence references, and concise outcomes. It does not expose private chain-of-thought.

### Adaptation / re-routing checkpoint

After a material reasoning result or new evidence, ask whether it materially changes any of:

- system characterization;
- a material entity/property;
- a derived structural obligation;
- a hypothesis;
- suspected root cause;
- abstraction level of the problem;
- relevant tradeoff;
- viable alternative set;
- required evidence;
- selected reasoning methods.

If no, continue the current bounded review.

If yes:

```text
Update the working system model
→ re-evaluate reasoning-method routing
→ activate only the smallest newly relevant method set
→ retire methods that are no longer decision-material
→ continue
```

Do not restart the entire review because one fact changed. Do not run all methods again. Keep the Method Coverage Ledger consistent with the reroute.

The same stop-at-sufficiency rule remains authoritative; adaptation is not permission for an infinite reflection loop.

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

### Finding-to-repair boundary

A confirmed symptom is not a confirmed root cause. Do not jump directly from a Finding to implementation merely because the manifestation is reproducible.

Before recommending a repair as root-correct, establish enough evidence for the causal mechanism and the boundary that actually owns or enforces it. If those remain unresolved, keep the root cause `NOT_PROVEN` and identify the smallest verification step that could discriminate between hypotheses.

When useful, apply the **surface-patch counterfactual**:

> If the current manifestation disappeared but the same causal mechanism appeared at another reachable instance, would this repair still prevent or deterministically expose the defect?

If not, treat the proposal as a surface patch unless evidence shows the defect class is genuinely single-instance and the local boundary is causal.

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

## 16. Guidance, validation, and proof

Do not confuse repository visibility with execution authority.

### Guidance

Repository-visible prose, examples, schemas, code, contracts, or policies can guide a model or human. Their existence proves that the guidance/artifact is present; it does not prove that a reviewer consumed it, that code ran, or that behavior was mechanically prevented.

### Validation

A validator or checker proves only the explicit predicates it actually executed on the supplied input. A schema PASS may prove shape and required-field constraints. A structural repository verifier may prove repository integrity predicates. Neither result, by itself, proves semantic engineering correctness, root-cause truth, architecture optimality, evidence completeness, or global LLM compliance.

Model-mediated invocation is still model-mediated: when an LLM can skip a requested command and no independent downstream gate rejects that bypass, the command is not an externally forced control path.

### Proof of mechanical control

A mechanical-enforcement claim requires evidence that an **externally forced execution path** ran the relevant control and that the path cannot be bypassed within the claimed boundary. The claim extends only to the exact machine-checkable predicates executed by that path.

For each claimed control, state or make clear:

- the failure it is intended to prevent;
- the exact machine-checkable predicate, if any;
- the executor that actually runs it;
- the consumer or gate that depends on its result;
- how the path can be bypassed, or why it cannot within scope.

If those facts are unknown, keep the control claim narrow. Deterministic code is justified by a real machine-executed purpose, not by a desire to make prompt-level guidance appear deterministic.

## Finding qualification boundary

Capability classes and qualification states answer different questions.

Capability issue shape, when applicable:

- `MISSING_CAPABILITY`
- `MISFIT_CAPABILITY`
- `EXCESS_CAPABILITY`

Qualification state:

- `CONFIRMED_FINDING`
- `JUSTIFIED_DEVIATION`
- `NOT_PROVEN`
- `NO_MATERIAL_ISSUE`

Do not force a capability class onto conclusions that are not capability-shape findings. The capability class describes **what kind of issue it is**; the qualification state describes **how strongly/resultfully the evidence supports the conclusion**.

## Stop rule

Additional reasoning is justified only if it can plausibly:

- reveal a material obligation/failure;
- change a finding's confidence or classification;
- change the leading repair family;
- expose a larger blast radius or tradeoff;
- invalidate an assumption;
- change the exact next engineering action.

Otherwise, stop.

A sufficient stop is always **scope-bounded**. “Enough evidence to choose the requested next action” is not equivalent to “repository-wide defect completeness is proven.” State what bounded decision/review scope is resolved and preserve any material unverified area that prevents a broader completeness claim.

## Control proportionality and anti-hardening overreach

Treat a proposed control, gate, validator, policy, evidence requirement, or enforcement mechanism as an engineering decision with cost and lifecycle consequences.

### Named-failure first

Before recommending a durable control, identify the material failure it is intended to prevent, detect, contain, or recover from. A vague desire for stronger governance is not sufficient. If the failure is still materially uncertain, perform bounded qualification instead of installing a permanent mechanism.

### Minimum effective control

Prefer the smallest control that adequately addresses the named failure within accepted authority and evidence. Evaluate materially lighter alternatives at the same abstraction level before choosing a stronger or more durable mechanism. Residual risk may be acceptable.

Keep the **policy question** (“why/when is control required?”) distinct from the **mechanism question** (“how is it applied?”). Correct policy does not automatically justify CI, a schema, a runtime guard, a registry, or another deterministic mechanism.

Blocking is exceptional rather than the default. Stronger prevention may be justified when consequence is serious, detection is difficult or delayed, recovery is destructive or expensive, external effects are material, or authority/security/data/money are materially involved. For quickly detectable and cheaply recoverable failures, prefer guidance, warning, sampling, or bounded review when those are sufficient.

Account for the control itself:

- human friction and interruption;
- runtime/token/context cost;
- interaction with existing controls;
- maintenance and change cost;
- coupling/dependencies introduced;
- disablement/removal cost.

Evaluate a proposed control inside the existing control set. Local usefulness does not prove good system composition.

Stop hardening when known material failures are adequately controlled, accepted, detectable, or recoverable and the next proposed control cannot justify its friction and lifecycle cost against a specific remaining material failure.

Do not invent numeric risk precision or mandatory FMEA machinery to make this judgment appear deterministic.

## Causal-core discovery and failure-class reasoning

Strengthen root-cause analysis only when added causal depth can change the engineering decision.

For a material finding, distinguish progressively when evidence supports it:

`manifestation → immediate mechanism → shared causal mechanism → governing system property/boundary → causal core`

The governing layer may be ownership, lifecycle, coupling, state, contract, composition, authority, or another system property that makes the failure class reachable. The causal core is the deepest material cause whose removal or containment would prevent, contain, or deterministically expose recurrence of that failure class.

When several findings plausibly share one mechanism, search across files/surfaces for common ownership, lifecycle, composition, state, boundary, or coupling causes. Do not manufacture a grand unified theory; shared-cause claims remain evidence-bounded and may stay `NOT_PROVEN`.

### Failure-class counterfactual

Before calling a repair root-correct for a recurring/systemic issue, ask:

> If this manifestation disappeared but the same underlying mechanism appeared at another reachable instance, would this repair still prevent, contain, or deterministically expose the defect class?

If not, treat it as a local/surface repair unless evidence establishes that the instance itself is the causal boundary.

Do **not** force every local defect into architecture depth. Continue deeper causal analysis only while the next layer can plausibly change the confirmed root cause, repair family, responsible owner/boundary, blast radius, verification method, recurrence risk, or exact next action. Otherwise stop.

A plausible architecture narrative is not causal proof. Use source/runtime evidence, history/co-change, differential cases, counterfactuals, or discriminating experiments when required to separate hypotheses.

## Lifecycle stage separation

Keep the review and delivery lifecycle semantically distinct:

`request / intake ≠ evidence ≠ assessment ≠ decision ≠ validation ≠ completion ≠ Owner delivery`

A prior stage may supply input to the next stage, but completion or PASS of one stage does not itself prove the next. Receiving a request is not evidence; collecting evidence is not assessment; assessment is not the final decision; selecting a decision is not validation; successful validation is not project/task completion; and technical completion is not Owner-facing delivery or Owner authorization.

This is a reasoning/reporting boundary, not a lifecycle state machine or workflow engine. More detailed implementation/test/CI/rereview stages remain separate where applicable.

## Decision/readiness state

For a material review output, end with one bounded decision-state headline:

- **GREEN** — current evidence is sufficient for the requested decision on the exact inspected target and no known material blocker remains for that action.
- **YELLOW** — a bounded repair, verification, qualification, rerun, clarification, or other specific action remains before the requested action can safely proceed.
- **RED** — do not proceed because a materially stronger stop condition exists, such as a serious confirmed blocker, invalid review identity, or failed required evidence/control boundary.

These are **not finding severity levels** and must not be derived mechanically from severity. GREEN is scope-bounded technical readiness for the requested action; it does not certify production/deployment/security/organizational readiness, Owner authorization, or absence of all possible defects. YELLOW must name the decision-changing issue and exact next action. RED is reserved for stronger stop conditions than ordinary repair/verification work.

Evidence maturity and finding classification/disposition remain separate dimensions.

## Root-cause-to-prompt pipeline

For a material actionable finding, do not move directly from Finding to a code-changing prompt.

Canonical semantic flow:

`Finding → Root-Cause Anchor → Root-Cause Qualification → Repair/Method Selection → Defect-Class Closure → Selected Method Conformance Lock → Falsification Obligations → Implementation / Verification Prompt`

### Root-Cause Anchor

Preserve only when material:

- observed manifestation;
- confirmed causal mechanism, or explicit `NOT_PROVEN`;
- evidence supporting the cause;
- affected invariant/obligation;
- ownership/enforcement/lifecycle boundary;
- same-root reachable instances or failure-class scope;
- important unknowns;
- the counterfactual explaining whether local repair is sufficient.

Do not turn this into mandatory bureaucracy for trivial findings.

### Root-Cause Qualification

If the repair family materially depends on a causal theory that remains unproven, do not generate a repair prompt. Generate the smallest discriminating qualification/verification prompt instead.

Finding ≠ Root Cause, and Root Cause ≠ Repair until the causal boundary is sufficiently qualified.

### Repair route: `BOUNDED` versus `FULL`

Use `BOUNDED` only when all material conditions hold:

- one bounded confirmed root cause covers the repair findings;
- one evidence-supported repair method is sufficient;
- no authority owner or source-of-truth migration is required;
- no public API/contract/schema/persisted-state migration is required;
- no runtime/process/isolation/topology migration is required;
- no coordinated external-consumer migration is required;
- no materially distinct evidence-supported competing method requires comparison;
- focused falsification can close the repair.

Otherwise use `FULL`.

Under `FULL`, separate unrelated root-cause groups, compare only materially distinct evidence-supported methods at the same abstraction level, do not invent alternatives to satisfy a quota, reject symptom-only methods when root-complete repair is feasible, and do not force a winner when evidence remains insufficient or methods are genuinely equivalent.

Material distinction concerns enforcement boundary, authority/SSOT ownership, validation mechanism, failure semantics, defect-class closure, public contract/schema migration, runtime topology, or consumer migration—not helper names or refactoring style.

#### Method-comparison priority

When `FULL` or another material decision genuinely leaves more than one admissible evidence-supported method to compare, consider decision factors in this order:

1. functional correctness / truthfulness;
2. defect-class closure / durability;
3. regression preservation / semantic blast radius;
4. authority / SSOT coherence / drift resistance;
5. falsifiability / proof strength;
6. proportionality / minimum effective control;
7. Owner operability / automation implications;
8. implementation / migration burden;
9. implementation time.

This is an **order of consideration, not a weighted scoring model**. Do not assign weights or trade away a higher-order correctness property merely because a lower-order option is faster or cheaper. Do not perform comparison theater when one sufficient evidence-backed method exists, do not manufacture alternatives to exercise the order, and do not force a winner when available evidence cannot materially distinguish equivalent methods. Time remains relevant, but it must not silently outrank correctness or defect-class closure.

### Selected Method Conformance Lock

Before a code-changing repair prompt, lock the material properties that define the selected method when applicable:

- enforcement boundary;
- authority owner;
- source-of-truth model;
- defect-class closure mechanism;
- failure semantics;
- API/schema/contract migration strategy;
- runtime/process/topology boundary;
- consumer migration boundary.

The implementer retains local freedom only where those properties do not change.

If implementation evidence shows the selected method cannot be implemented while preserving the lock, report `SELECTED_METHOD_INFEASIBLE` and return to method selection. Do not silently substitute another architecture or surface patch.

### Falsification obligations

Repair evidence must be capable of disproving the selected method, not merely proving that new code executes. When applicable include:

- original-defect reproduction;
- repaired behavior;
- same-root/future-drift instance;
- enforcement-boundary bypass;
- nonconforming-method distinction;
- positive control;
- directly affected regression control;
- real consumer integration when a real consumer exists;
- exact-target/exact-Head re-verification.

Proposed tests are not executed evidence. A conformance check is weak if both the selected method and a materially different nonconforming method can pass without an observable distinction.

### Executor handoff contract

For code-changing repair handoffs, default to these top-level sections unless the target executor requires an equivalent structure:

```text
[IMPLEMENTATION CONTRACT]
[VALIDATION CONTRACT]
[POST-IMPLEMENTATION REPORT]
```

The prompt is an execution artifact, not new authority.

The Implementation Contract should preserve the bounded outcome, exact target identity when known, confirmed root cause/invariants, selected method and correct boundary, applicable Conformance Lock, scope/prohibited changes, and stop behavior if the lock cannot be preserved.

The Validation Contract should contain falsification, focused regressions, expected state outcomes, exact-target/freshness checks when applicable, and truthful `NOT_PROVEN` handling for unavailable environment/platform evidence.

The Post-Implementation Report must keep lifecycle stages distinct: implementation completed ≠ selected-method conformance ≠ focused tests ≠ regression tests ≠ exact-Head CI ≠ fresh rereview ≠ merge/release/Owner authorization.

When material, the Post-Implementation Report should state compactly:

- what was actually implemented;
- whether selected-method conformance is `PROVEN` or `NOT_PROVEN`;
- focused falsification/test results;
- affected regression results;
- exact-Head CI/current verification status;
- fresh rereview status where required;
- remaining blockers or unknowns;
- planned-versus-actual deviations;
- the exact resulting target identity / resulting Head;
- which claims are backed by executed evidence versus unavailable or unverified evidence.

Implementation success does not imply validation success, and CI success does not imply rereview, merge/release, or Owner authorization. Keep the report as a bounded handoff, not a certificate system, evidence registry, Run-ID mechanism, or acceptance bureaucracy.