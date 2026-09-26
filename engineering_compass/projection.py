from __future__ import annotations

from typing import Any

from .model import require, require_dict, validate_evidence_bundle
from .root_cause import validate_assessment

ACTION_ROUTING = {
    "STOP_AT_SUFFICIENCY": {"recipient": "none", "may_modify_code": False, "prompt_required": False, "prompt_kind": None},
    "COLLECT_EVIDENCE": {"recipient": "reviewer_model", "may_modify_code": False, "prompt_required": True, "prompt_kind": "verification_prompt"},
    "VERIFY_ROOT_CAUSE": {"recipient": "reviewer_model", "may_modify_code": False, "prompt_required": True, "prompt_kind": "verification_prompt"},
    "COMPLETE_REPAIR_DESIGN": {"recipient": "reviewer_model", "may_modify_code": False, "prompt_required": True, "prompt_kind": "repair_design_prompt"},
    "OWNER_DECISION_REQUIRED": {"recipient": "project_owner", "may_modify_code": False, "prompt_required": False, "prompt_kind": None},
    "SPECIALIST_REVIEW_REQUIRED": {"recipient": "domain_specialist", "may_modify_code": False, "prompt_required": True, "prompt_kind": "specialist_review_prompt"},
    "IMPLEMENT_REPAIR": {"recipient": "implementer_model", "may_modify_code": True, "prompt_required": True, "prompt_kind": "implementation_prompt"},
    "RERUN_REVIEW": {"recipient": "reviewer_model", "may_modify_code": False, "prompt_required": True, "prompt_kind": "fresh_review_prompt"},
}


def _group_by_id(assessment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {group["group_id"]: group for group in assessment.get("root_cause_groups", [])}


def _material_evidence_gaps(evidence: dict[str, Any], assessment: dict[str, Any]) -> list[str]:
    gaps = [str(item) for item in evidence["completeness"].get("material_gaps", [])]
    gaps.extend(str(item) for item in assessment.get("unverified_areas", []) if str(item))
    return list(dict.fromkeys(gaps))


def project_action(evidence_bundle: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    """Deterministically project next action from validated evidence + bounded LLM judgment."""
    validate_evidence_bundle(evidence_bundle)
    routes = validate_assessment(evidence_bundle, assessment)
    reasons: list[str] = []

    if evidence_bundle["freshness"] != "CURRENT":
        action = "RERUN_REVIEW"
        reasons.append("target_not_current")
    else:
        gaps = _material_evidence_gaps(evidence_bundle, assessment)
        if gaps:
            action = "COLLECT_EVIDENCE"
            reasons.extend(f"material_gap:{item}" for item in gaps)
        elif assessment.get("specialist_review_required") is True:
            action = "SPECIALIST_REVIEW_REQUIRED"
            reasons.append("specialist_review_required")
        elif assessment.get("owner_policy_decision_required") is True:
            action = "OWNER_DECISION_REQUIRED"
            reasons.append("owner_policy_decision_required")
        else:
            findings = assessment.get("findings", [])
            repair_findings = [f for f in findings if f.get("qualification") == "CONFIRMED_FINDING" and f.get("repair_disposition") == "REPAIR"]
            verify_findings = [f for f in findings if f.get("repair_disposition") == "VERIFY" or f.get("qualification") == "NOT_PROVEN"]
            if verify_findings and not repair_findings:
                action = "COLLECT_EVIDENCE"
                reasons.extend(f"unresolved_finding:{f['finding_id']}" for f in verify_findings)
            elif repair_findings:
                groups = _group_by_id(assessment)
                selected_groups: list[str] = []
                action = "IMPLEMENT_REPAIR"
                for finding in repair_findings:
                    group = groups[finding["root_cause_group_id"]]
                    anchor_state = group["anchor"]["state"]
                    if anchor_state != "CONFIRMED":
                        action = "VERIFY_ROOT_CAUSE"
                        reasons.append(f"root_cause_not_confirmed:{group['group_id']}")
                        break
                    selection = group["selection"]
                    if selection["state"] == "INSUFFICIENT_EVIDENCE":
                        action = "COLLECT_EVIDENCE"
                        reasons.append(f"method_selection_insufficient:{group['group_id']}")
                        break
                    if selection["state"] == "EQUIVALENT_FINALISTS":
                        action = "OWNER_DECISION_REQUIRED"
                        reasons.append(f"equivalent_finalists:{group['group_id']}")
                        break
                    if not group.get("conformance_lock") or not group.get("falsification_obligations"):
                        action = "COMPLETE_REPAIR_DESIGN"
                        reasons.append(f"repair_design_incomplete:{group['group_id']}")
                        break
                    selected_groups.append(group["group_id"])
                if action == "IMPLEMENT_REPAIR":
                    reasons.extend(f"root_complete_repair_ready:{gid}:{routes[gid]}" for gid in sorted(set(selected_groups)))
            else:
                action = "STOP_AT_SUFFICIENCY"
                reasons.append("no_confirmed_repair_obligation")

    route = ACTION_ROUTING[action]
    projection = {
        "schema_version": 1,
        "action": action,
        "recipient": route["recipient"],
        "may_modify_code": route["may_modify_code"],
        "prompt_required": route["prompt_required"],
        "prompt_kind": route["prompt_kind"],
        "reason_codes": reasons,
        "target_binding": {
            "repository": evidence_bundle["target"]["repository"],
            "kind": evidence_bundle["target"]["kind"],
            "head_sha": evidence_bundle["identity"].get("head_sha"),
        },
    }
    validate_projection(projection)
    return projection


def validate_projection(projection: dict[str, Any]) -> None:
    require(projection.get("schema_version") == 1, "action projection schema_version must be 1")
    action = projection.get("action")
    require(action in ACTION_ROUTING, f"unknown action: {action}")
    route = ACTION_ROUTING[action]
    for field in ("recipient", "may_modify_code", "prompt_required", "prompt_kind"):
        require(projection.get(field) == route[field], f"projection {field} diverges from canonical routing")
    require_dict(projection.get("target_binding"), "projection.target_binding")
