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

Projection evaluates the complete validated state first and applies this precedence globally; it does not stop at the first Finding or root-cause group encountered.

1. stale/non-current target → `RERUN_REVIEW`;
2. material evidence/unverified gaps → `COLLECT_EVIDENCE`;
3. explicit specialist requirement → `SPECIALIST_REVIEW_REQUIRED`;
4. owner policy decision required → `OWNER_DECISION_REQUIRED`;
5. any authorized repair group with unconfirmed root cause → `VERIFY_ROOT_CAUSE`;
6. any authorized repair group with insufficient/incomplete method-selection evidence → `COLLECT_EVIDENCE`;
7. any authorized repair group with equivalent finalists → `OWNER_DECISION_REQUIRED`;
8. any authorized selected repair without complete Conformance Lock/falsification → `COMPLETE_REPAIR_DESIGN`;
9. all authorized repair groups root-complete and selected → `IMPLEMENT_REPAIR`;
10. no remaining material repair/verification obligation → `STOP_AT_SUFFICIENCY`.

The action and reason ordering are invariant under reordering of Findings and root-cause groups. `IMPLEMENT_REPAIR` also carries the sorted canonical `authorized_repair_group_ids`; non-modifying actions carry no repair authorization.

The runtime does not create new Findings or root causes during projection. Projection consumes structured judgment; it does not replace it.

## Freshness preflight and authorization payload

Before applying normal action precedence, projection validates the evidence contract and syntactic assessment binding. Valid binding drift or a non-current bundle projects RERUN_REVIEW; malformed/cross-target input fails closed. Only CURRENT_MATCH proceeds to full assessment validation.

IMPLEMENT_REPAIR carries the canonical Finding-granular authorization mapping. Non-modifying actions carry no implementation authorization.

## Live freshness authority boundary

Persisted `evidence.freshness` is evidence metadata, not action-time authority. The public `project_action()` boundary reconstructs the canonical collection request from the reviewed target selectors and review intent, recollects through `GitHubEvidenceCollector`, and only then applies the deterministic projection to the live bundle. The pure `_project_action_current()` helper exists only for internal deterministic tests/fixture verification and is not an externally consumable modification-authority boundary.

A successful live recollection whose material identity/digest differs from the reviewed assessment flows through the existing binding preflight and produces `RERUN_REVIEW`. GitHub collection failure propagates as a blocking contract failure, so no modification-capable projection is emitted. No TTL or Head-only shortcut is accepted because material same-Head evidence can change.
