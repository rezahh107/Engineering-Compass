from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

TARGET_KINDS = {"PR_SCOPE", "REF_DELTA_SCOPE", "REPOSITORY_SCOPE"}
TARGET_SELECTOR_KEYS = {
    "PR_SCOPE": {"kind", "repository", "pr_number"},
    "REF_DELTA_SCOPE": {"kind", "repository", "base_ref", "target_ref"},
    "REPOSITORY_SCOPE": {"kind", "repository", "ref"},
}
EVIDENCE_SURFACES_BY_TARGET = {
    "PR_SCOPE": {
        "changed_file_inventory",
        "diff_content",
        "reviews",
        "conversation_comments",
        "inline_review_comments",
        "checks",
        "commit_statuses",
        "review_threads",
    },
    "REF_DELTA_SCOPE": {"changed_file_inventory", "diff_content"},
    "REPOSITORY_SCOPE": {"repository_tree_inventory", "repository_source_content"},
}
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



def canonical_target(target: dict[str, Any]) -> dict[str, Any]:
    target = require_dict(target, "target")
    kind = target.get("kind")
    require(kind in TARGET_KINDS, f"target.kind must be one of {sorted(TARGET_KINDS)}")
    allowed = TARGET_SELECTOR_KEYS[kind]
    extra, missing = set(target) - allowed, allowed - set(target)
    require(not extra, f"{kind} target contains unsupported selector keys: {sorted(extra)}")
    require(not missing, f"{kind} target missing required selector keys: {sorted(missing)}")
    repo = require_string(target.get("repository"), "target.repository")
    require(REPO_RE.fullmatch(repo) is not None, "target.repository must use owner/name")
    if kind == "PR_SCOPE":
        pr = target.get("pr_number")
        require(isinstance(pr, int) and not isinstance(pr, bool) and pr > 0, "PR_SCOPE requires positive pr_number")
        return {"kind": kind, "repository": repo, "pr_number": pr}
    if kind == "REF_DELTA_SCOPE":
        return {"kind": kind, "repository": repo, "base_ref": require_string(target.get("base_ref"), "target.base_ref"), "target_ref": require_string(target.get("target_ref"), "target.target_ref")}
    return {"kind": kind, "repository": repo, "ref": require_string(target.get("ref"), "target.ref")}


def validate_target(target: dict[str, Any]) -> None:
    canonical_target(target)


def validate_request(request: dict[str, Any]) -> None:
    require_dict(request, "request")
    extra = set(request) - {"target", "review_intent", "inspection_profile"}
    require(not extra, f"caller request contains unsupported fields: {sorted(extra)}")
    canonical_target(require_dict(request.get("target"), "request.target"))
    require_string(request.get("review_intent"), "request.review_intent")
    require(request.get("inspection_profile", "deep") in {"focused", "deep"}, "inspection_profile must be focused or deep")


def compute_review_intent_digest(review_intent: str) -> str:
    value = require_string(review_intent, "review_intent")
    material = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(material).hexdigest()}"



def _evidence_digest_payload(bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": bundle.get("schema_version"),
        "target": bundle.get("target"),
        "identity": bundle.get("identity"),
        "freshness": bundle.get("freshness"),
        "completeness": bundle.get("completeness"),
        "evidence_records": bundle.get("evidence_records"),
    }


def compute_evidence_digest(bundle: dict[str, Any]) -> str:
    material = json.dumps(
        _evidence_digest_payload(bundle),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(material).hexdigest()}"



def finalize_evidence_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    bundle["target"] = canonical_target(require_dict(bundle.get("target"), "evidence.target"))
    review_intent = require_string(bundle.get("review_intent"), "evidence.review_intent")
    bundle["review_intent_digest"] = compute_review_intent_digest(review_intent)
    bundle["evidence_digest"] = compute_evidence_digest(bundle)
    return bundle


def _validate_sha40(value: Any, path: str) -> str:
    require(isinstance(value, str) and SHA40_RE.fullmatch(value) is not None, f"{path} must be lowercase SHA-40")
    return value


def _validate_sha256(value: Any, path: str) -> str:
    require(isinstance(value, str) and SHA256_RE.fullmatch(value) is not None, f"{path} must be sha256:<64 lowercase hex chars>")
    return value



def validate_evidence_bundle(bundle: dict[str, Any]) -> None:
    version = bundle.get("schema_version")
    require(version == 2, f"evidence schema_version must be 2 (got {version!r}); regenerate evidence under the current snapshot-binding contract")
    target = canonical_target(require_dict(bundle.get("target"), "evidence.target"))
    require(bundle.get("target") == target, "evidence.target must be canonical")
    review_intent = require_string(bundle.get("review_intent"), "evidence.review_intent")
    intent_digest = _validate_sha256(bundle.get("review_intent_digest"), "evidence.review_intent_digest")
    require(intent_digest == compute_review_intent_digest(review_intent), "review_intent_digest does not match review_intent")
    identity = require_dict(bundle.get("identity"), "evidence.identity")
    require_string(identity.get("repository_id"), "evidence.identity.repository_id")
    _validate_sha40(identity.get("head_sha"), "evidence.identity.head_sha")
    kind = target["kind"]
    if kind in {"PR_SCOPE", "REF_DELTA_SCOPE"}:
        require_string(identity.get("base_ref"), "evidence.identity.base_ref")
        _validate_sha40(identity.get("base_sha"), "evidence.identity.base_sha")
        require_string(identity.get("head_ref"), "evidence.identity.head_ref")
        _validate_sha40(identity.get("merge_base_sha"), "evidence.identity.merge_base_sha")
    require(bundle.get("freshness") in FRESHNESS, f"evidence.freshness must be one of {sorted(FRESHNESS)}")
    completeness = require_dict(bundle.get("completeness"), "evidence.completeness")
    full_coverage = completeness.get("full_coverage")
    require(isinstance(full_coverage, bool), "completeness.full_coverage must be boolean")
    material_gaps = require_list(completeness.get("material_gaps", []), "completeness.material_gaps")
    surfaces = require_dict(completeness.get("surfaces"), "completeness.surfaces")
    required_surfaces = EVIDENCE_SURFACES_BY_TARGET[kind]
    missing_surfaces = sorted(required_surfaces - set(surfaces))
    require(not missing_surfaces, f"evidence completeness missing required surfaces for {kind}: {missing_surfaces}")
    for surface in required_surfaces:
        require(
            isinstance(surfaces.get(surface), bool),
            f"completeness.surfaces.{surface} must be boolean",
        )
    incomplete_surfaces = sorted(surface for surface in required_surfaces if surfaces[surface] is not True)
    if incomplete_surfaces:
        require(not full_coverage, "incomplete evidence surfaces cannot coexist with full_coverage=true")
        require(bool(material_gaps), "incomplete evidence surfaces require an explicit material gap")
    ids=[]
    for index, record in enumerate(require_list(bundle.get("evidence_records", []), "evidence.evidence_records")):
        obj=require_dict(record,f"evidence_records[{index}]")
        ids.append(require_string(obj.get("evidence_id"), f"evidence_records[{index}].evidence_id"))
        require_string(obj.get("kind"), f"evidence_records[{index}].kind")
        require_string(obj.get("source"), f"evidence_records[{index}].source")
        require_list(obj.get("limitations", []), f"evidence_records[{index}].limitations")
    require(len(ids)==len(set(ids)), "evidence_id values must be unique")
    digest=_validate_sha256(bundle.get("evidence_digest"), "evidence.evidence_digest")
    require(digest==compute_evidence_digest(bundle), "evidence_digest does not match the material evidence snapshot")


def expected_target_binding(bundle: dict[str, Any]) -> dict[str, Any]:
    target, identity = bundle["target"], bundle["identity"]
    common={"repository":target["repository"],"repository_id":identity["repository_id"],"kind":target["kind"],"head_sha":identity["head_sha"],"evidence_digest":bundle["evidence_digest"],"review_intent_digest":bundle["review_intent_digest"]}
    if target["kind"]=="PR_SCOPE":
        common.update({"pr_number":target["pr_number"],"base_ref":identity["base_ref"],"base_sha":identity["base_sha"],"head_ref":identity["head_ref"],"merge_base_sha":identity["merge_base_sha"]})
    elif target["kind"]=="REF_DELTA_SCOPE":
        common.update({"base_ref":target["base_ref"],"base_sha":identity["base_sha"],"target_ref":target["target_ref"],"merge_base_sha":identity["merge_base_sha"]})
    else:
        common["ref"]=target["ref"]
    return common


def _validate_target_binding_shape(binding: dict[str, Any], bundle: dict[str, Any]) -> dict[str, Any]:
    expected=expected_target_binding(bundle)
    require(not (set(expected)-set(binding)), f"assessment target binding missing mandatory fields: {sorted(set(expected)-set(binding))}")
    require(not (set(binding)-set(expected)), f"assessment target binding contains unsupported fields: {sorted(set(binding)-set(expected))}")
    require_string(binding.get("repository"), "assessment.target_binding.repository")
    require_string(binding.get("repository_id"), "assessment.target_binding.repository_id")
    kind=binding.get("kind")
    require(kind in TARGET_KINDS and kind==bundle["target"]["kind"], "assessment target binding kind does not match target kind")
    _validate_sha40(binding.get("head_sha"), "assessment.target_binding.head_sha")
    _validate_sha256(binding.get("evidence_digest"), "assessment.target_binding.evidence_digest")
    _validate_sha256(binding.get("review_intent_digest"), "assessment.target_binding.review_intent_digest")
    if kind=="PR_SCOPE":
        pr=binding.get("pr_number"); require(isinstance(pr,int) and not isinstance(pr,bool) and pr>0,"assessment.target_binding.pr_number must be positive")
        require_string(binding.get("base_ref"),"assessment.target_binding.base_ref"); _validate_sha40(binding.get("base_sha"),"assessment.target_binding.base_sha")
        require_string(binding.get("head_ref"),"assessment.target_binding.head_ref"); _validate_sha40(binding.get("merge_base_sha"),"assessment.target_binding.merge_base_sha")
    elif kind=="REF_DELTA_SCOPE":
        require_string(binding.get("base_ref"),"assessment.target_binding.base_ref"); _validate_sha40(binding.get("base_sha"),"assessment.target_binding.base_sha")
        require_string(binding.get("target_ref"),"assessment.target_binding.target_ref"); _validate_sha40(binding.get("merge_base_sha"),"assessment.target_binding.merge_base_sha")
    else:
        require_string(binding.get("ref"),"assessment.target_binding.ref")
    return expected


def preflight_assessment_binding(evidence_bundle: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    validate_evidence_bundle(evidence_bundle)
    assessment=require_dict(assessment,"assessment")
    version=assessment.get("assessment_version")
    require(version==2, f"assessment_version must be 2 (got {version!r}); regenerate assessment under the current snapshot-binding contract")
    binding=require_dict(assessment.get("target_binding"),"assessment.target_binding")
    expected=_validate_target_binding_shape(binding,evidence_bundle)
    stable={"repository","repository_id","kind"}
    kind=evidence_bundle["target"]["kind"]
    stable |= {"pr_number"} if kind=="PR_SCOPE" else ({"base_ref","target_ref"} if kind=="REF_DELTA_SCOPE" else {"ref"})
    unrelated=sorted(k for k in stable if binding.get(k)!=expected.get(k))
    require(not unrelated,f"assessment target binding refers to a different target: {unrelated}")
    mismatched=sorted(k for k,v in expected.items() if binding.get(k)!=v)
    return {"state":"CURRENT_MATCH" if not mismatched else "STALE_OR_SUPERSEDED_REVIEW","mismatched_fields":mismatched,"previous_binding":dict(binding),"current_binding":expected}


def validate_target_binding(binding: dict[str, Any], bundle: dict[str, Any]) -> None:
    expected=_validate_target_binding_shape(binding,bundle)
    for key,value in expected.items():
        require(binding.get(key)==value,f"assessment target binding mismatch for {key}")


def evidence_ids(bundle: dict[str, Any]) -> set[str]:
    return {str(item["evidence_id"]) for item in bundle.get("evidence_records", [])}


def require_refs(refs: Iterable[Any], allowed: set[str], path: str) -> None:
    values = list(refs)
    require(all(isinstance(item, str) and item for item in values), f"{path} must contain non-empty string IDs")
    missing = sorted(set(values) - allowed)
    require(not missing, f"{path} contains unknown evidence refs: {missing}")
