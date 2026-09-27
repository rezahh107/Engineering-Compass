# LLM Assessment Contract

The LLM supplies engineering judgment; the runtime validates its structure, evidence binding, repair authorization, and transition eligibility.

## Snapshot binding

Evidence contract v2 includes a deterministic `evidence_digest` over material target identity, completeness state, and evidence content. Intentionally volatile collection metadata such as `collected_at_epoch` is excluded from the digest.

Assessment contract v2 binds to that exact digest and to target-specific selectors/identity:

- all modes: repository, repository ID, kind, Head SHA, evidence digest;
- `PR_SCOPE`: PR number plus Base/Head refs and SHAs and merge-base identity;
- `REF_DELTA_SCOPE`: Base/target selectors plus resolved Base/Head and merge-base identity;
- `REPOSITORY_SCOPE`: requested ref plus resolved Head.

An assessment produced for a materially different evidence snapshot at the same Head is therefore stale and must fail closed. Contract-v1 evidence/assessment shapes are not silently accepted.

## Repair authorization

The runtime derives one canonical repair-authorization set from confirmed Findings whose `repair_disposition` is `REPAIR`.

For every `REPAIR` Finding, its `root_cause_group_id` must exist and that exact Finding ID must appear in the referenced group's `finding_ids`. A group being `SELECTED` is not authorization by itself.

The same derived authorized group set is consumed by projection and, only after `IMPLEMENT_REPAIR`, by Prompt-Pipeline handoff. Handoff must not independently reinterpret which selected groups are authorized.

## Selected-method consistency

Every repair method declares the Conformance-Lock decision properties: enforcement boundary, authority owner, source-of-truth model, defect-class closure mechanism, failure semantics, contract/API migration strategy, and consumer migration boundary.

For a selected method, the Conformance Lock must match those properties exactly. When the Root-Cause Anchor is confirmed, the lock's enforcement boundary must also equal the anchor's confirmed enforcement boundary.

Under `FULL`, materially competing admissible methods require complete comparison in the documented canonical order before a `SELECTED` state can authorize implementation. The runtime validates completeness and evidence binding; it does not infer the objectively best method.

## Falsification

Selected repair design is implementation-ready only when falsification contains required obligations, including a required defect-class check and a required selected-method-deviation check. All-optional or vacuous obligations route to repair-design completion rather than code modification.

## Separation of authority

The runtime can reject an internally inconsistent assessment. It cannot prove that a semantically plausible root cause is true merely because the JSON is valid.

Therefore evidence references must resolve to the bound evidence bundle; confirmed findings require evidence; confirmed root causes require evidence and an enforcement boundary; selected methods must satisfy mandatory admissibility; uncertainty remains uncertainty.

## Coverage

Only materially activated reasoning methods belong in the Method Coverage Ledger. `APPLIED_NO_FINDING` and `NOT_EXECUTED` are distinct states; the ledger is not a universal checklist.
