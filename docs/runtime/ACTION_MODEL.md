# Canonical Action Model

The runtime converts validated evidence + bounded model assessment into exactly one next action.

| Action | Recipient | Code modification | Prompt |
|---|---|---:|---:|
| `STOP_AT_SUFFICIENCY` | none | no | no |
| `COLLECT_EVIDENCE` | reviewer model | no | yes |
| `VERIFY_ROOT_CAUSE` | reviewer model | no | yes |
| `COMPLETE_REPAIR_DESIGN` | reviewer model | no | yes |
| `OWNER_DECISION_REQUIRED` | project owner | no | no |
| `SPECIALIST_REVIEW_REQUIRED` | domain specialist | no | yes |
| `IMPLEMENT_REPAIR` | implementer model | yes | yes |
| `RERUN_REVIEW` | reviewer model | no | yes |

## Projection precedence

1. stale/non-current target → `RERUN_REVIEW`;
2. material evidence/unverified gaps → `COLLECT_EVIDENCE`;
3. explicit specialist requirement → `SPECIALIST_REVIEW_REQUIRED`;
4. owner policy decision required → `OWNER_DECISION_REQUIRED`;
5. confirmed repair finding with unconfirmed root cause → `VERIFY_ROOT_CAUSE`;
6. insufficient method-selection evidence → `COLLECT_EVIDENCE`;
7. equivalent finalists → `OWNER_DECISION_REQUIRED`;
8. selected repair without required lock/falsification → `COMPLETE_REPAIR_DESIGN`;
9. root-complete selected repair → `IMPLEMENT_REPAIR`;
10. no remaining material repair/verification obligation → `STOP_AT_SUFFICIENCY`.

The runtime does not create new Findings or root causes during projection. Projection consumes structured judgment; it does not replace it.
