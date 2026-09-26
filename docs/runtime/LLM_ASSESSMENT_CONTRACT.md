# LLM Assessment Contract

The LLM supplies engineering judgment; the runtime validates its structure and transition eligibility.

An assessment is bound to the exact target repository/kind/Head from the evidence bundle and contains:

- Method Coverage Ledger;
- material findings with evidence references;
- optional capability class (`MISSING_CAPABILITY | MISFIT_CAPABILITY | EXCESS_CAPABILITY`);
- repair disposition;
- root-cause groups;
- candidate repair methods and ordered comparison evidence;
- method selection state;
- Conformance Lock for every selected repair;
- falsification obligations;
- unverified areas;
- owner/specialist escalation flags;
- stop reason.

## Separation of authority

The runtime can reject an internally inconsistent assessment. It cannot prove that a semantically plausible root cause is true merely because the JSON is valid.

Therefore evidence references must resolve to the evidence bundle; confirmed findings require evidence; confirmed root causes require evidence and an enforcement boundary; selected methods must satisfy mandatory admissibility; no direct implementation action is available until Conformance Lock and falsification obligations exist; uncertainty remains uncertainty.

## Coverage

Only materially activated reasoning methods belong in the Method Coverage Ledger. `APPLIED_NO_FINDING` and `NOT_EXECUTED` are distinct states; the ledger is not a universal checklist.
