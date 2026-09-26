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
    return tuple(str(props.get(key, "")) for key in (
        "enforcement_boundary",
        "authority_owner",
        "failure_semantics",
        "contract_or_api_migration_strategy",
    ))


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


def _validate_selection(group: dict[str, Any], methods: list[dict[str, Any]], route: str) -> None:
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


def _validate_lock_and_falsification(group: dict[str, Any]) -> None:
    selection = group["selection"]
    if selection["state"] != "SELECTED":
        return
    lock = require_dict(group.get("conformance_lock"), "group.conformance_lock")
    require(lock.get("selected_method_id") == selection.get("selected_method_id"), "conformance lock must bind selected method")
    locked = require_dict(lock.get("locked_properties"), "conformance_lock.locked_properties")
    for key in LOCKED_PROPERTIES:
        require_string(locked.get(key), f"conformance_lock.locked_properties.{key}")
    require_list(lock.get("allowed_local_freedom", []), "conformance_lock.allowed_local_freedom")
    forbidden = require_list(lock.get("forbidden_deviations", []), "conformance_lock.forbidden_deviations")
    require("replacing_the_selected_method" in forbidden, "conformance lock must forbid selected-method replacement")
    obligations = require_list(group.get("falsification_obligations"), "group.falsification_obligations")
    require(obligations, "selected repair requires falsification obligations")
    ids: set[str] = set()
    for index, value in enumerate(obligations):
        item = require_dict(value, f"falsification_obligations[{index}]")
        oid = require_string(item.get("obligation_id"), f"falsification_obligations[{index}].obligation_id")
        require(oid not in ids, f"duplicate falsification obligation: {oid}")
        ids.add(oid)
        require_string(item.get("kind"), f"falsification_obligations[{index}].kind")
        require_string(item.get("expected_observable"), f"falsification_obligations[{index}].expected_observable")
        require(isinstance(item.get("required", True), bool), "falsification required flag must be boolean")


def validate_assessment(evidence_bundle: dict[str, Any], assessment: dict[str, Any]) -> dict[str, str]:
    """Validate LLM-produced assessment without pretending to generate the judgment."""
    validate_evidence_bundle(evidence_bundle)
    require(assessment.get("assessment_version") == 1, "assessment_version must be 1")
    allowed_evidence = evidence_ids(evidence_bundle)
    binding = require_dict(assessment.get("target_binding"), "assessment.target_binding")
    evidence_identity = evidence_bundle["identity"]
    require(binding.get("repository") == evidence_bundle["target"]["repository"], "assessment repository binding mismatch")
    require(binding.get("kind") == evidence_bundle["target"]["kind"], "assessment target kind binding mismatch")
    require(binding.get("head_sha") == evidence_identity.get("head_sha"), "assessment head binding mismatch")
    _validate_method_coverage(assessment, allowed_evidence)
    findings = _validate_findings(assessment, allowed_evidence)
    groups = require_list(assessment.get("root_cause_groups", []), "assessment.root_cause_groups")
    group_ids: set[str] = set()
    routes: dict[str, str] = {}
    for index, value in enumerate(groups):
        group = require_dict(value, f"root_cause_groups[{index}]")
        gid = require_string(group.get("group_id"), f"root_cause_groups[{index}].group_id")
        require(gid not in group_ids, f"duplicate root-cause group: {gid}")
        group_ids.add(gid)
        _validate_anchor(group, findings, allowed_evidence)
        methods = _validate_methods(group, allowed_evidence)
        route = determine_repair_route(group, methods)
        declared = group.get("route")
        require(declared in {None, route}, f"root-cause group {gid} declares {declared}, runtime requires {route}")
        group["route"] = route
        _validate_selection(group, methods, route)
        _validate_lock_and_falsification(group)
        routes[gid] = route
    repair_findings = [f for f in findings.values() if f.get("repair_disposition") == "REPAIR"]
    for finding in repair_findings:
        require(finding["root_cause_group_id"] in group_ids, f"repair finding {finding['finding_id']} lacks a valid root-cause group")
    require_list(assessment.get("unverified_areas", []), "assessment.unverified_areas")
    require(isinstance(assessment.get("owner_policy_decision_required", False), bool), "owner_policy_decision_required must be boolean")
    require(isinstance(assessment.get("specialist_review_required", False), bool), "specialist_review_required must be boolean")
    require_string(assessment.get("stop_reason", "not yet sufficient"), "assessment.stop_reason")
    return routes
