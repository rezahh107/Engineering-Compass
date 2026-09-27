from __future__ import annotations

from typing import Any

from .model import expected_target_binding, require, require_dict, validate_evidence_bundle
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
    return sorted(set(gaps))


def project_action(evidence_bundle: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    """Project one canonical action from the complete validated state, independent of input ordering."""
    validate_evidence_bundle(evidence_bundle)
    validation = validate_assessment(evidence_bundle, assessment)
    reasons: list[str] = []
    authorized_group_ids = list(validation["authorized_repair_group_ids"])

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
        elif authorized_group_ids:
            groups = _group_by_id(assessment)
            authorized_groups = [groups[gid] for gid in authorized_group_ids]
            root_unconfirmed = sorted(
                group["group_id"] for group in authorized_groups if group["anchor"]["state"] != "CONFIRMED"
            )
            selection_insufficient = sorted(
                group["group_id"]
                for group in authorized_groups
                if group["selection"]["state"] == "INSUFFICIENT_EVIDENCE"
                or not validation["selection_evidence_complete"][group["group_id"]]
            )
            equivalent = sorted(
                group["group_id"] for group in authorized_groups if group["selection"]["state"] == "EQUIVALENT_FINALISTS"
            )
            design_incomplete = sorted(
                group["group_id"]
                for group in authorized_groups
                if group["selection"]["state"] == "SELECTED"
                and not validation["repair_design_complete"][group["group_id"]]
            )

            if root_unconfirmed:
                action = "VERIFY_ROOT_CAUSE"
                reasons.extend(f"root_cause_not_confirmed:{gid}" for gid in root_unconfirmed)
            elif selection_insufficient:
                action = "COLLECT_EVIDENCE"
                reasons.extend(f"method_selection_insufficient:{gid}" for gid in selection_insufficient)
            elif equivalent:
                action = "OWNER_DECISION_REQUIRED"
                reasons.extend(f"equivalent_finalists:{gid}" for gid in equivalent)
            elif design_incomplete:
                action = "COMPLETE_REPAIR_DESIGN"
                reasons.extend(f"repair_design_incomplete:{gid}" for gid in design_incomplete)
            else:
                action = "IMPLEMENT_REPAIR"
                reasons.extend(
                    f"root_complete_repair_ready:{gid}:{validation['routes'][gid]}" for gid in authorized_group_ids
                )
        else:
            findings = assessment.get("findings", [])
            verify_findings = sorted(
                f["finding_id"]
                for f in findings
                if f.get("repair_disposition") == "VERIFY" or f.get("qualification") == "NOT_PROVEN"
            )
            if verify_findings:
                action = "COLLECT_EVIDENCE"
                reasons.extend(f"unresolved_finding:{fid}" for fid in verify_findings)
            else:
                action = "STOP_AT_SUFFICIENCY"
                reasons.append("no_confirmed_repair_obligation")

    route = ACTION_ROUTING[action]
    projection = {
        "schema_version": 2,
        "action": action,
        "recipient": route["recipient"],
        "may_modify_code": route["may_modify_code"],
        "prompt_required": route["prompt_required"],
        "prompt_kind": route["prompt_kind"],
        "reason_codes": reasons,
        "authorized_repair_group_ids": authorized_group_ids if action == "IMPLEMENT_REPAIR" else [],
        "target_binding": expected_target_binding(evidence_bundle),
    }
    validate_projection(projection)
    return projection


def validate_projection(projection: dict[str, Any]) -> None:
    require(projection.get("schema_version") == 2, "action projection schema_version must be 2")
    action = projection.get("action")
    require(action in ACTION_ROUTING, f"unknown action: {action}")
    route = ACTION_ROUTING[action]
    for field in ("recipient", "may_modify_code", "prompt_required", "prompt_kind"):
        require(projection.get(field) == route[field], f"projection {field} diverges from canonical routing")
    groups = projection.get("authorized_repair_group_ids")
    require(isinstance(groups, list), "projection authorized_repair_group_ids must be a list")
    require(groups == sorted(set(groups)), "projection authorized_repair_group_ids must be sorted and unique")
    if action == "IMPLEMENT_REPAIR":
        require(bool(groups), "IMPLEMENT_REPAIR requires authorized repair groups")
    else:
        require(not groups, "non-modifying action must not carry authorized repair groups")
    require_dict(projection.get("target_binding"), "projection.target_binding")
