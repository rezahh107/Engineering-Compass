# Mission and Boundaries

## Mission

Engineering Compass governs the **use of engineering expertise** by an LLM.

The model is assumed to already know many engineering techniques. The repository's job is to help it determine:

- what kind of engineering situation it is facing;
- which reasoning or investigation methods are materially relevant;
- in what order those methods should be applied;
- what new evidence should cause the method sequence to adapt;
- how deep the investigation should go;
- when additional analysis is no longer decision-material.

Short form:

> The repository governs the use of engineering expertise; it does not contain or re-teach all engineering expertise.

## Desired outcome

A review should improve the quality of engineering **decisions**, not merely count code defects.

The reviewer should be able to move from local implementation detail to the system-level reason the detail exists, while still avoiding speculative redesign and unnecessary complexity.

## North Star

For each material issue:

> Find the deepest **material** cause, then prefer the smallest system-level improvement that removes or properly contains that cause without creating greater overall cost.

`deepest` without `material` is over-analysis.

`smallest` without `root-correct` is patching symptoms.

## Primary review units

The preferred review unit is a **material engineering decision**, such as:

- depending on an internal API;
- choosing exact-version admission;
- introducing persistent state;
- adding a retry/queue/cache/lock;
- creating a second source of truth;
- choosing a data structure or algorithm;
- establishing a compatibility or failure policy.

Changed lines are evidence of decisions; they are not the whole review model.

## Non-goals

Engineering Compass is not intended to:

- replace CI, linters, type checkers, static analyzers, or security scanners;
- duplicate language/framework documentation;
- encode thousands of known anti-patterns;
- assume every theoretical improvement is worth implementing;
- force modernization of healthy code;
- treat model confidence as evidence;
- optimize implementation before questioning whether the implementation strategy should exist;
- make product/owner decisions that require business authority.

## Two scopes, one reasoning model

### PR scope

Focus on new or materially changed decisions and their consequences. Read beyond the diff only where needed to understand intent, dependencies, boundaries, blast radius, or historical coupling.

### Repository scope

Build a broader system model and look for architectural drift, recurring risk themes, cross-module coupling, missing capabilities, misplaced responsibilities, and system-wide simplification opportunities.

The reasoning rules remain the same; only scope and evidence depth change.
