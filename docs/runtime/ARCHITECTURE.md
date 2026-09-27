# Executable Review Runtime Architecture

## Purpose

Engineering Compass has an executable **control plane** around LLM engineering judgment.

It deliberately does not replace the LLM with deterministic heuristics. The model still performs semantic engineering work; the runtime controls identity, exact evidence-snapshot binding, structured assessment, root-cause repair authorization, action routing, and Prompt-Pipeline handoff.

## Stage separation

```text
caller intent
→ exact target evidence + deterministic evidence digest
→ LLM engineering assessment bound to that snapshot
→ root-cause / repair-design validation
→ canonical authorized-repair set
→ global action projection
→ Prompt-Pipeline intake
→ external Prompt-Pipeline generation from verified executable checkout
→ implementation / verification agent
→ fresh evidence and rereview
```

`request != evidence != assessment != repair authorization != action != prompt artifact != implementation != validation != completion`

## Target modes

- `PR_SCOPE`: repository + PR number; GitHub resolves Base, Head, changed files, checks, reviews, comments, and merge-base evidence.
- `REF_DELTA_SCOPE`: repository + base ref + target ref; GitHub compare resolves exact identities and changed files.
- `REPOSITORY_SCOPE`: repository + exact or symbolic ref; GitHub resolves a commit snapshot and recursive tree inventory.

Caller input expresses intent and target selectors. It is not authority for resolved SHA, changed files, checks, findings, root causes, or actions.

## Runtime modules

- `engineering_compass.github_evidence` — read-only GitHub REST evidence collection plus deterministic material-snapshot digest.
- `engineering_compass.root_cause` — validates model-produced findings, relational repair authorization, root-cause anchors, candidate methods, FULL comparison completeness, selected-method/Lock consistency, and falsification obligations.
- `engineering_compass.projection` — derives all applicable conditions from the complete validated state and applies canonical precedence globally.
- `engineering_compass.prompt_pipeline` — serializes only projection-authorized repair groups, verifies the pinned external executable checkout, and invokes Prompt-Pipeline without auto-approving its review state.
- `engineering_compass.cli` — command-line boundary.

## Claim boundary

The runtime does **not** mechanically prove that the model found every relevant fact, that a root-cause statement is objectively true, that the selected method is globally optimal, or that a generated prompt will force target-model compliance.

It does mechanically reject known invalid transitions such as stale snapshot reuse, contradictory selected method/Lock/Anchor properties, unauthorized selected groups entering implementation handoff, incomplete FULL comparison reaching implementation, vacuous falsification, first-match projection precedence, or dirty Prompt-Pipeline executable source.

## Freshness

Evidence contract v2 fingerprints material evidence content and target identity while excluding intentionally volatile collection time. Assessment contract v2 binds to that digest plus target-specific selectors/identity. A later material snapshot at the same Head therefore requires a new assessment; no stale repair-ready state is carried forward.
