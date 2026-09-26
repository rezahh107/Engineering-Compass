from __future__ import annotations

import re
from typing import Any, Iterable

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

TARGET_KINDS = {"PR_SCOPE", "REF_DELTA_SCOPE", "REPOSITORY_SCOPE"}
FRESHNESS = {"CURRENT", "STALE", "UNKNOWN"}
QUALIFICATION_STATES = {
    "CONFIRMED_FINDING",
    "JUSTIFIED_DEVIATION",
    "NOT_PROVEN",
    "NO_MATERIAL_ISSUE",
}
CAPABILITY_CLASSES = {None, "MISSING_CAPABILITY", "MISFIT_CAPABILITY", "EXCESS_CAPABILITY"}
METHOD_STATUSES = {"APPLIED_FINDING", "APPLIED_NO_FINDING", "NOT_EXECUTED", "BLOCKED"}
ROOT_CAUSE_STATES = {"CONFIRMED", "NOT_PROVEN", "NOT_ASSESSABLE"}
SELECTION_STATES = {"SELECTED", "EQUIVALENT_FINALISTS", "INSUFFICIENT_EVIDENCE"}
REPAIR_DISPOSITIONS = {"REPAIR", "VERIFY", "ACCEPT_DEVIATION", "NONE"}

COMPARISON_CRITERIA = [
    "functional_correctness_truthfulness",
    "defect_class_closure_durability",
    "regression_preservation_blast_radius",
    "authority_ssot_coherence_drift_resistance",
    "deterministic_proof_strength",
    "project_proportionality",
    "owner_operability_automation",
    "implementation_migration_burden",
    "implementation_time",
]

LOCKED_PROPERTIES = [
    "enforcement_boundary",
    "authority_owner",
    "source_of_truth_model",
    "defect_class_closure_mechanism",
    "failure_semantics",
    "contract_or_api_migration_strategy",
    "consumer_migration_boundary",
]


class ContractError(ValueError):
    """Raised when a structured review contract is invalid or unsafe to advance."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def require_string(value: Any, path: str, *, nonempty: bool = True) -> str:
    require(isinstance(value, str), f"{path} must be a string")
    if nonempty:
        require(bool(value.strip()), f"{path} must be non-empty")
    return value


def require_list(value: Any, path: str) -> list[Any]:
    require(isinstance(value, list), f"{path} must be a list")
    return value


def require_dict(value: Any, path: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{path} must be an object")
    return value


def validate_target(target: dict[str, Any]) -> None:
    kind = target.get("kind")
    require(kind in TARGET_KINDS, f"target.kind must be one of {sorted(TARGET_KINDS)}")
    repo = require_string(target.get("repository"), "target.repository")
    require(REPO_RE.fullmatch(repo) is not None, "target.repository must use owner/name")
    if kind == "PR_SCOPE":
        pr = target.get("pr_number")
        require(isinstance(pr, int) and not isinstance(pr, bool) and pr > 0, "PR_SCOPE requires positive pr_number")
    elif kind == "REF_DELTA_SCOPE":
        require_string(target.get("base_ref"), "target.base_ref")
        require_string(target.get("target_ref"), "target.target_ref")
    elif kind == "REPOSITORY_SCOPE":
        require_string(target.get("ref", "main"), "target.ref")


def validate_request(request: dict[str, Any]) -> None:
    require_dict(request, "request")
    validate_target(require_dict(request.get("target"), "request.target"))
    require_string(request.get("review_intent"), "request.review_intent")
    profile = request.get("inspection_profile", "deep")
    require(profile in {"focused", "deep"}, "inspection_profile must be focused or deep")
    forbidden = {
        "head_sha",
        "base_sha",
        "merge_base_sha",
        "changed_files",
        "checks",
        "findings",
        "root_cause",
        "decision",
    }
    overlap = forbidden.intersection(request)
    require(not overlap, f"caller request contains fact/judgment authority fields: {sorted(overlap)}")


def validate_evidence_bundle(bundle: dict[str, Any]) -> None:
    require(bundle.get("schema_version") == 1, "evidence schema_version must be 1")
    validate_target(require_dict(bundle.get("target"), "evidence.target"))
    identity = require_dict(bundle.get("identity"), "evidence.identity")
    require_string(identity.get("repository_id"), "evidence.identity.repository_id")
    head = identity.get("head_sha")
    if head is not None:
        require(isinstance(head, str) and SHA40_RE.fullmatch(head) is not None, "head_sha must be lowercase SHA-40")
    base = identity.get("base_sha")
    if base is not None:
        require(isinstance(base, str) and SHA40_RE.fullmatch(base) is not None, "base_sha must be lowercase SHA-40")
    merge_base = identity.get("merge_base_sha")
    if merge_base is not None:
        require(isinstance(merge_base, str) and SHA40_RE.fullmatch(merge_base) is not None, "merge_base_sha must be lowercase SHA-40")
    require(bundle.get("freshness") in FRESHNESS, f"evidence.freshness must be one of {sorted(FRESHNESS)}")
    completeness = require_dict(bundle.get("completeness"), "evidence.completeness")
    require(isinstance(completeness.get("full_coverage"), bool), "completeness.full_coverage must be boolean")
    require_list(completeness.get("material_gaps", []), "completeness.material_gaps")
    records = require_list(bundle.get("evidence_records", []), "evidence.evidence_records")
    ids: list[str] = []
    for index, record in enumerate(records):
        obj = require_dict(record, f"evidence_records[{index}]")
        ids.append(require_string(obj.get("evidence_id"), f"evidence_records[{index}].evidence_id"))
        require_string(obj.get("kind"), f"evidence_records[{index}].kind")
        require_string(obj.get("source"), f"evidence_records[{index}].source")
    require(len(ids) == len(set(ids)), "evidence_id values must be unique")


def evidence_ids(bundle: dict[str, Any]) -> set[str]:
    return {str(item["evidence_id"]) for item in bundle.get("evidence_records", [])}


def require_refs(refs: Iterable[Any], allowed: set[str], path: str) -> None:
    values = list(refs)
    require(all(isinstance(item, str) and item for item in values), f"{path} must contain non-empty string IDs")
    missing = sorted(set(values) - allowed)
    require(not missing, f"{path} contains unknown evidence refs: {missing}")
