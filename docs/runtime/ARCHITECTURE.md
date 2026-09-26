# Executable Review Runtime Architecture

## Purpose

Engineering Compass now has an executable **control plane** around LLM engineering judgment.

It deliberately does not replace the LLM with deterministic heuristics. The model still performs semantic engineering work; the runtime controls identity, evidence boundaries, structured assessment, root-cause repair admission, action routing, and Prompt-Pipeline handoff.

## Stage separation

```text
caller intent
→ exact target evidence
→ LLM engineering assessment
→ root-cause / repair-design validation
→ canonical action projection
→ Prompt-Pipeline intake
→ external Prompt-Pipeline generation
→ implementation / verification agent
→ fresh evidence and rereview
```

`request != evidence != assessment != repair design != action != prompt artifact != implementation != validation != completion`

## Target modes

- `PR_SCOPE`: repository + PR number; GitHub resolves Base, Head, changed files, checks, reviews, comments, and merge-base evidence.
- `REF_DELTA_SCOPE`: repository + base ref + target ref; GitHub compare resolves exact identities and changed files.
- `REPOSITORY_SCOPE`: repository + exact or symbolic ref; GitHub resolves a commit snapshot and recursive tree inventory.

Caller input expresses intent and target selectors. It is not authority for resolved SHA, changed files, checks, findings, root causes, or actions.

## Runtime modules

- `engineering_compass.github_evidence` — read-only GitHub REST evidence collection.
- `engineering_compass.root_cause` — validates model-produced findings, root-cause anchors, candidate methods, comparison order, selection, Conformance Lock, and falsification obligations.
- `engineering_compass.projection` — deterministic next-action routing from validated evidence + assessment.
- `engineering_compass.prompt_pipeline` — builds canonical Prompt-Pipeline intake, verifies the locked external checkout, and invokes Prompt-Pipeline without auto-approving its review state.
- `engineering_compass.cli` — command-line boundary.

## Claim boundary

The runtime does **not** mechanically prove that the model found every relevant fact, that a root-cause statement is objectively true, that the selected method is globally optimal, or that a generated prompt will force target-model compliance.

It does mechanically reject known invalid transitions such as direct Finding→patch prompt, unbound target identity, pseudo-alternatives, numeric score substitution, or missing Conformance Lock before code-modifying action.

## Freshness

Assessments bind to the exact resolved Head when a Head exists. A later Head change requires a new evidence bundle and affected review stages must be rerun. No stale repair-ready state is carried forward.
