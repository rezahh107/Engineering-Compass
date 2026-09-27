from __future__ import annotations

from typing import Any

from .model import (
    CAPABILITY_CLASSES,
    COMPARISON_CRITERIA,
    LOCKED_PROPERTIES,
    METHOD_STATUSES,
    QUALIFICATION_STATES,
    REPAIR_DISPOSITIONS,
    ROOT_CAUSE_STATES,
    SELECTION_STATES,
    ContractError,
    evidence_ids,
    require,
    require_dict,
    require_list,
    require_refs,
    require_string,
    validate_evidence_bundle,
    validate_target_binding,
)

MATERIAL_CHANGE_FLAGS = {
    "authority_or_ssot_change",
    "public_contract_or_schema_migration",
    "runtime_topology_change",
    "external_consumer_migration",
    "competing_material_methods",
}

ADMISSIBILITY_KEYS = {
    "functional_truth",
    "defect_class_closure",
    "fail_closed_truthfulness",
    "authority_ssot_preservation",
    "mechanical_falsifiability",
    "regression_preservation",
    "bounded_scope",
    "no_unsupported_assumptions",
}


DEFECT_CLASS_FALSIFICATION_KINDS = {
    "original_defect_reproduction",
    "defect_class_closure",
    "same_root_cause_future_drift",
}


def _validate_method_coverage(assessment: dict[str, Any], allowed_evidence: set[str]) -> None:
    ledger = require_list(assessment.get("method_coverage", []), "assessment.method_coverage")
    names: set[str] = set()
    for index, item in enumerate(ledger):
        entry = require_dict(item, f"method_coverage[{index}]")
        method = require_string(entry.get("method"), f"method_coverage[{index}].method")
        require(method not in names, f"duplicate method coverage entry: {method}")
        names.add(method)
        require_string(entry.get("trigger"), f"method_coverage[{index}].trigger")
        require(entry.get("status") in METHOD_STATUSES, f"invalid method coverage status for {method}")
        require_refs(entry.get("evidence_refs", []), allowed_evidence, f"method_coverage[{index}].evidence_refs")
        require_string(entry.get("outcome"), f"method_coverage[{index}].outcome")


def _validate_findings(assessment: dict[str, Any], allowed_evidence: set[str]) -> dict[str, dict[str, Any]]:
    findings = require_list(assessment.get("findings", []), "assessment.findings")
    by_id: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(findings):
        finding = require_dict(value, f"findings[{index}]")
        fid = require_string(finding.get("finding_id"), f"findings[{index}].finding_id")
        require(fid not in by_id, f"duplicate finding_id: {fid}")
        require(finding.get("qualification") in QUALIFICATION_STATES, f"invalid qualification for {fid}")
        capability_class = finding.get("capability_class")
        require(capability_class in CAPABILITY_CLASSES, f"invalid capability_class for {fid}")
        require(finding.get("repair_disposition", "NONE") in REPAIR_DISPOSITIONS, f"invalid repair_disposition for {fid}")
        require_refs(finding.get("evidence_refs", []), allowed_evidence, f"findings[{index}].evidence_refs")
        if finding.get("qualification") == "CONFIRMED_FINDING":
            require(bool(finding.get("evidence_refs")), f"confirmed finding {fid} requires evidence")
        if finding.get("repair_disposition") == "REPAIR":
            require_string(finding.get("root_cause_group_id"), f"findings[{index}].root_cause_group_id")
        by_id[fid] = finding
    return by_id


def _validate_anchor(group: dict[str, Any], findings: dict[str, dict[str, Any]], allowed_evidence: set[str]) -> None:
    anchor = require_dict(group.get("anchor"), f"root_cause_group[{group.get('group_id')}].anchor")
    state = anchor.get("state")
    require(state in ROOT_CAUSE_STATES, f"invalid root cause state in {group.get('group_id')}")
    require_string(anchor.get("observed_symptom"), "anchor.observed_symptom")
    require_string(anchor.get("confirmed_root_cause", "unknown"), "anchor.confirmed_root_cause")
    require_refs(anchor.get("root_cause_evidence", []), allowed_evidence, "anchor.root_cause_evidence")
    require_list(anchor.get("affected_invariants", []), "anchor.affected_invariants")
    require_string(anchor.get("correct_enforcement_boundary", "unknown"), "anchor.correct_enforcement_boundary")
    require_list(anchor.get("same_root_cause_instances", []), "anchor.same_root_cause_instances")
    require_list(anchor.get("valid_behavior_to_preserve", []), "anchor.valid_behavior_to_preserve")
    require_list(anchor.get("explicit_unknowns", []), "anchor.explicit_unknowns")
    if state == "CONFIRMED":
        require(anchor.get("confirmed_root_cause") not in {"unknown", "UNKNOWN"}, "confirmed root cause cannot be unknown")
        require(bool(anchor.get("root_cause_evidence")), "confirmed root cause requires evidence")
        require(anchor.get("correct_enforcement_boundary") not in {"unknown", "UNKNOWN"}, "confirmed root cause requires enforcement boundary")

    group_findings = set(require_list(group.get("finding_ids", []), "group.finding_ids"))
    require(group_findings, "root-cause group must reference at least one finding")
    missing = group_findings - set(findings)
    require(not missing, f"root-cause group references unknown findings: {sorted(missing)}")


def _method_signature(method: dict[str, Any]) -> tuple[str, ...]:
    props = require_dict(method.get("decision_properties", {}), "method.decision_properties")
    return tuple(str(props.get(key, "")) for key in LOCKED_PROPERTIES)


def _validate_methods(group: dict[str, Any], allowed_evidence: set[str]) -> list[dict[str, Any]]:
    methods = require_list(group.get("methods", []), "group.methods")
    ids: set[str] = set()
    signatures: dict[tuple[str, ...], str] = {}
    for index, value in enumerate(methods):
        method = require_dict(value, f"methods[{index}]")
        mid = require_string(method.get("method_id"), f"methods[{index}].method_id")
        require(mid not in ids, f"duplicate method_id: {mid}")
        ids.add(mid)
        require_string(method.get("summary"), f"methods[{index}].summary")
        decision_properties = require_dict(method.get("decision_properties"), f"methods[{index}].decision_properties")
        for key in LOCKED_PROPERTIES:
            require_string(decision_properties.get(key), f"methods[{index}].decision_properties.{key}")
        admissibility = require_dict(method.get("admissibility"), f"methods[{index}].admissibility")
        missing_adm = ADMISSIBILITY_KEYS - set(admissibility)
        require(not missing_adm, f"method {mid} missing admissibility fields: {sorted(missing_adm)}")
        require(all(isinstance(admissibility[k], bool) for k in ADMISSIBILITY_KEYS), f"method {mid} admissibility values must be boolean")
        require_refs(method.get("evidence_refs", []), allowed_evidence, f"methods[{index}].evidence_refs")
        differences = require_list(method.get("decision_relevant_differences", []), f"methods[{index}].decision_relevant_differences")
        require(all(isinstance(item, str) and item for item in differences), f"method {mid} decision differences must be strings")
        comparison = require_list(method.get("comparison", []), f"methods[{index}].comparison")
        if comparison:
            criteria = [item.get("criterion") for item in comparison if isinstance(item, dict)]
            require(criteria == COMPARISON_CRITERIA[: len(criteria)], f"method {mid} comparison criteria must follow canonical order")
            for c_index, entry in enumerate(comparison):
                c = require_dict(entry, f"methods[{index}].comparison[{c_index}]")
                require_string(c.get("criterion"), f"methods[{index}].comparison[{c_index}].criterion")
                require_string(c.get("assessment"), f"methods[{index}].comparison[{c_index}].assessment")
                require_refs(c.get("evidence_refs", []), allowed_evidence, f"methods[{index}].comparison[{c_index}].evidence_refs")
                require("score" not in c and "weight" not in c, "numeric scoring/weights are forbidden")
        sig = _method_signature(method)
        if len(methods) > 1 and sig in signatures:
            raise ContractError(f"methods {signatures[sig]} and {mid} are not materially distinct at the decision level")
        signatures[sig] = mid
    return methods


def determine_repair_route(group: dict[str, Any], methods: list[dict[str, Any]]) -> str:
    flags = require_dict(group.get("material_change_flags", {}), "group.material_change_flags")
    unknown = set(flags) - MATERIAL_CHANGE_FLAGS
    require(not unknown, f"unknown material_change_flags: {sorted(unknown)}")
    for key in MATERIAL_CHANGE_FLAGS:
        require(isinstance(flags.get(key, False), bool), f"material_change_flags.{key} must be boolean")
    admissible = [m for m in methods if all(m["admissibility"].get(k) is True for k in ADMISSIBILITY_KEYS)]
    if any(flags.get(key, False) for key in MATERIAL_CHANGE_FLAGS) or len(admissible) != 1:
        return "FULL"
    return "BOUNDED"


def _full_comparison_complete(methods: list[dict[str, Any]]) -> bool:
    admissible = [m for m in methods if all(m["admissibility"].get(k) is True for k in ADMISSIBILITY_KEYS)]
    if len(admissible) <= 1:
        return True
    for method in admissible:
        comparison = method.get("comparison", [])
        if len(comparison) != len(COMPARISON_CRITERIA):
            return False
        if [entry.get("criterion") for entry in comparison] != COMPARISON_CRITERIA:
            return False
        if not any(entry.get("evidence_refs") for entry in comparison):
            return False
    return True


def _validate_selection(group: dict[str, Any], methods: list[dict[str, Any]], route: str) -> bool:
    selection = require_dict(group.get("selection"), "group.selection")
    state = selection.get("state")
    require(state in SELECTION_STATES, f"invalid selection state: {state}")
    method_ids = {m["method_id"] for m in methods}
    selected = selection.get("selected_method_id")
    if state == "SELECTED":
        require(selected in method_ids, "selected_method_id must reference a candidate method")
        chosen = next(m for m in methods if m["method_id"] == selected)
        require(all(chosen["admissibility"].get(k) is True for k in ADMISSIBILITY_KEYS), "selected method must satisfy all mandatory admissibility conditions")
        require_string(selection.get("rationale"), "selection.rationale")
    else:
        require(selected in {None, ""}, "non-selected state must not carry selected_method_id")
    if route == "BOUNDED":
        require(state == "SELECTED", "BOUNDED route requires a selected method")
    if route == "FULL" and state == "SELECTED":
        return _full_comparison_complete(methods)
    return True



def _repair_design_missing(group: dict[str, Any], methods: list[dict[str, Any]]) -> list[str]:
    selection = group["selection"]
    if selection["state"] != "SELECTED":
        return ["selected_method_not_selected"]
    missing: list[str] = []
    lock_value = group.get("conformance_lock")
    obligations_value = group.get("falsification_obligations", [])
    if not lock_value:
        missing.append("conformance_lock_missing")
    else:
        lock = require_dict(lock_value, "group.conformance_lock")
        require(lock.get("selected_method_id") == selection.get("selected_method_id"), "conformance lock must bind selected method")
        locked = require_dict(lock.get("locked_properties"), "conformance_lock.locked_properties")
        chosen = next(method for method in methods if method["method_id"] == selection["selected_method_id"])
        decision_properties = require_dict(chosen.get("decision_properties"), "selected_method.decision_properties")
        for key in LOCKED_PROPERTIES:
            value = require_string(locked.get(key), f"conformance_lock.locked_properties.{key}")
            require(value == decision_properties.get(key), f"conformance lock {key} contradicts selected method")
        anchor = require_dict(group.get("anchor"), "group.anchor")
        if anchor.get("state") == "CONFIRMED":
            require(locked["enforcement_boundary"] == anchor.get("correct_enforcement_boundary"), "conformance lock enforcement_boundary contradicts confirmed root-cause anchor")
        require_list(lock.get("allowed_local_freedom", []), "conformance_lock.allowed_local_freedom")
        forbidden = require_list(lock.get("forbidden_deviations", []), "conformance_lock.forbidden_deviations")
        require("replacing_the_selected_method" in forbidden, "conformance lock must forbid selected-method replacement")
    obligations = require_list(obligations_value, "group.falsification_obligations")
    if not obligations:
        missing.append("falsification_obligations_missing")
        return missing
    ids: set[str] = set()
    required_kinds: set[str] = set()
    for index, value in enumerate(obligations):
        item = require_dict(value, f"falsification_obligations[{index}]")
        oid = require_string(item.get("obligation_id"), f"falsification_obligations[{index}].obligation_id")
        require(oid not in ids, f"duplicate falsification obligation: {oid}")
        ids.add(oid)
        kind = require_string(item.get("kind"), f"falsification_obligations[{index}].kind")
        require_string(item.get("expected_observable"), f"falsification_obligations[{index}].expected_observable")
        required = item.get("required", True)
        require(isinstance(required, bool), "falsification required flag must be boolean")
        if required:
            required_kinds.add(kind)
    if not required_kinds:
        missing.append("required_falsification_obligation_missing")
    if "selected_method_deviation" not in required_kinds:
        missing.append("selected_method_deviation_check_missing")
    if not (required_kinds & DEFECT_CLASS_FALSIFICATION_KINDS):
        missing.append("defect_class_falsification_check_missing")
    return missing



def validate_assessment(evidence_bundle: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    """Validate current assessment and derive the sole Finding-granular repair authorization state."""
    validate_evidence_bundle(evidence_bundle)
    version = assessment.get("assessment_version")
    require(version == 2, f"assessment_version must be 2 (got {version!r}); regenerate assessment under the current snapshot-binding contract")
    allowed_evidence = evidence_ids(evidence_bundle)
    binding = require_dict(assessment.get("target_binding"), "assessment.target_binding")
    validate_target_binding(binding, evidence_bundle)
    _validate_method_coverage(assessment, allowed_evidence)
    findings = _validate_findings(assessment, allowed_evidence)
    groups = require_list(assessment.get("root_cause_groups", []), "assessment.root_cause_groups")
    group_ids: set[str] = set()
    groups_by_id: dict[str, dict[str, Any]] = {}
    routes: dict[str, str] = {}
    selection_evidence_complete: dict[str, bool] = {}
    repair_design_complete: dict[str, bool] = {}
    repair_design_missing: dict[str, list[str]] = {}
    for index, value in enumerate(groups):
        group = require_dict(value, f"root_cause_groups[{index}]")
        gid = require_string(group.get("group_id"), f"root_cause_groups[{index}].group_id")
        require(gid not in group_ids, f"duplicate root-cause group: {gid}")
        group_ids.add(gid); groups_by_id[gid] = group
        _validate_anchor(group, findings, allowed_evidence)
        methods = _validate_methods(group, allowed_evidence)
        route = determine_repair_route(group, methods)
        declared = group.get("route")
        require(declared in {None, route}, f"root-cause group {gid} declares {declared}, runtime requires {route}")
        selection_evidence_complete[gid] = _validate_selection(group, methods, route)
        missing = _repair_design_missing(group, methods)
        repair_design_missing[gid] = missing
        repair_design_complete[gid] = not missing
        routes[gid] = route

    repair_findings = [f for f in findings.values() if f.get("repair_disposition") == "REPAIR"]
    for finding in repair_findings:
        gid = finding["root_cause_group_id"]
        require(gid in group_ids, f"repair finding {finding['finding_id']} lacks a valid root-cause group")
        require(finding["finding_id"] in groups_by_id[gid].get("finding_ids", []), f"repair finding {finding['finding_id']} is not present in root-cause group {gid}.finding_ids")
    for gid, group in groups_by_id.items():
        for fid in group.get("finding_ids", []):
            finding = findings[fid]
            if finding.get("repair_disposition") == "REPAIR":
                require(finding.get("root_cause_group_id") == gid, f"repair finding {fid} is attached to conflicting root-cause groups")

    authorized_by_group: dict[str, list[str]] = {}
    for finding in repair_findings:
        if finding.get("qualification") == "CONFIRMED_FINDING":
            authorized_by_group.setdefault(finding["root_cause_group_id"], []).append(finding["finding_id"])
    authorized_by_group = {gid: sorted(set(authorized_by_group[gid])) for gid in sorted(authorized_by_group)}
    authorized_findings = sorted(fid for ids in authorized_by_group.values() for fid in ids)
    authorized_groups = sorted(authorized_by_group)

    require_list(assessment.get("unverified_areas", []), "assessment.unverified_areas")
    require(isinstance(assessment.get("owner_policy_decision_required", False), bool), "owner_policy_decision_required must be boolean")
    specialist_required = assessment.get("specialist_review_required", False)
    require(isinstance(specialist_required, bool), "specialist_review_required must be boolean")
    specialist_scope = assessment.get("specialist_review_scope")
    if specialist_required:
        require_string(specialist_scope, "assessment.specialist_review_scope")
    elif specialist_scope is not None:
        require_string(specialist_scope, "assessment.specialist_review_scope")
    require_string(assessment.get("stop_reason", "not yet sufficient"), "assessment.stop_reason")
    return {
        "routes": routes,
        "authorized_repair_finding_ids": authorized_findings,
        "authorized_repair_group_ids": authorized_groups,
        "authorized_repair_finding_ids_by_group": authorized_by_group,
        "selection_evidence_complete": selection_evidence_complete,
        "repair_design_complete": repair_design_complete,
        "repair_design_missing": repair_design_missing,
    }
