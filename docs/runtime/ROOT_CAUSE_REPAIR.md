# Root-Complete Repair Runtime

## Invariant

No direct `Finding → Implementation Prompt` transition is permitted.

```text
Finding(s)
→ Root-Cause Anchor
→ canonical authorized-repair set
→ BOUNDED or FULL repair route
→ materially distinct admissible methods
→ method selection
→ defect-class closure
→ Selected Method Conformance Lock
→ required falsification obligations
→ canonical action projection
→ Prompt-Pipeline handoff
```

A root-cause group is implementation-eligible only when at least one confirmed `REPAIR` Finding authorizes that exact group. `selection.state=SELECTED` alone never grants implementation authority.

## Root-Cause Anchor

Every repair group binds finding IDs, observed symptom, root-cause state (`CONFIRMED | NOT_PROVEN | NOT_ASSESSABLE`), causal mechanism when established, evidence, affected invariants, correct enforcement boundary, same-root-cause instances, behavior to preserve, and explicit unknowns.

A confirmed symptom is not a confirmed cause. If the causal mechanism or enforcement boundary is not established, the runtime routes to verification rather than code modification.

Every `REPAIR` Finding must point to an existing root-cause group, and that group must contain the exact Finding ID. Conflicting reverse membership is rejected.

## Surface-patch counterfactual

Before selecting a method ask: if the current manifestation disappeared but the same causal mechanism appeared at another reachable instance, would this repair still prevent or deterministically expose the defect? If not, it is a symptom patch unless evidence proves the defect class is genuinely single-instance and the local boundary is causal.

## Route selection

`BOUNDED` is available only when exactly one admissible method remains and no material authority/SSOT, public contract/schema, runtime topology, external-consumer migration, or competing-method flag is present. Otherwise the route is `FULL`.

Under `FULL`, candidate methods must be materially distinct at a decision-relevant level. Pseudo-alternatives with the same locked decision properties are rejected.

## Comparison order

No numeric scoring or weighted average is allowed. Methods are compared in canonical order:

1. functional correctness and truthfulness;
2. defect-class closure and durability;
3. regression preservation and semantic blast radius;
4. authority/SSOT coherence and drift resistance;
5. deterministic proof strength;
6. project proportionality;
7. owner operability/automation;
8. implementation/migration burden;
9. implementation time.

When multiple admissible methods materially compete on a `FULL` route, each must carry the complete ordered comparison with evidence binding before `SELECTED` can reach implementation. Empty or partial comparison routes to evidence collection. If finalists remain genuinely equivalent, route to `OWNER_DECISION_REQUIRED` rather than inventing a winner.

## Mandatory admissibility

A selected method must satisfy functional truth, defect-class closure, fail-closed truthfulness, authority/SSOT preservation, mechanical falsifiability, regression preservation, bounded scope, and absence of unsupported assumptions that invalidate the method.

## Conformance Lock

A selected method declares and locks enforcement boundary, authority owner, source-of-truth model, defect-class closure mechanism, failure semantics, contract/API migration strategy, and consumer migration boundary. The lock must equal the selected method on those properties, and its enforcement boundary must agree with a confirmed Root-Cause Anchor.

Local implementation details may vary only when they preserve those properties. The lock must forbid replacing the selected method. If implementation evidence shows the method cannot be executed while preserving the lock, the implementer must stop and report `SELECTED_METHOD_INFEASIBLE` rather than silently switching architectures.

## Falsification

Selected repairs require executable falsification obligations. At least one obligation must be required, and implementation readiness requires a required defect-class check plus a required selected-method-deviation check. Applicable defect-class checks include original-defect reproduction, explicit defect-class closure, and same-root-cause/future-drift checks.

A conformance test is too weak if materially different/nonconforming methods can pass without a deterministic observable difference.

## Finding-granular modification authority

Root-cause grouping and modification authority are separate. validate_assessment derives authorized_repair_finding_ids_by_group from only CONFIRMED_FINDING + REPAIR Findings. A mixed root-cause group may retain non-authorized context, but those siblings cannot be serialized as authorized implementation Findings or gain modification authority from group membership.
