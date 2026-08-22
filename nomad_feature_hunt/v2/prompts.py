from __future__ import annotations

import json
from typing import Any

from .constants import OUTPUT_LIMIT_BYTES, PROMPT_LIMIT_BYTES
from .schemas import FAMILY_FIELDS, OUTPUT_FIELDS, PARAMETER_FIELDS, SPEC_FIELDS


class PromptLimitError(ValueError):
    pass


ROLE_CONTRACTS = {
    "evidence_curator": "Return sources and Atlas gaps as one object.",
    "family_architect": "Return exactly three FamilyCards in family_cards.",
    "spec_builder": "Return exactly two FeatureSpecs in feature_specs.",
    "plugin_writer": (
        "Return plugin_source only when the assigned family cannot use a trusted kernel; "
        "it must define compute_family(structure, config)."
    ),
    "target_exploiter": "Return one or two adaptive FeatureSpecs from categorical discovery feedback.",
    "cross_family_synthesizer": "Return one or two physically declared coupling FeatureSpecs.",
    "experimental_analyst": "Return receipt-bound analysis; matrix and score receipt IDs are mandatory.",
    "blind_judge": "Return receipt-bound blinded judgments; do not infer unavailable scores.",
    "memory_curator": "Classify only controller-supplied receipt IDs; do not invent features.",
}


def _ensure_limit(prompt: str) -> str:
    size = len(prompt.encode("utf-8"))
    if size > PROMPT_LIMIT_BYTES:
        raise PromptLimitError(f"prompt is {size} bytes; limit is {PROMPT_LIMIT_BYTES}")
    return prompt


def build_role_prompt(
    role: dict[str, Any],
    *,
    evidence: list[dict[str, Any]],
    novelty_summary: dict[str, Any],
    controller_context: dict[str, Any] | None = None,
) -> str:
    if len(evidence) > 10:
        raise PromptLimitError("a role may receive at most ten claim-level sources")
    contract = ROLE_CONTRACTS.get(str(role.get("class")))
    if contract is None:
        raise ValueError(f"unsupported role class: {role.get('class')}")
    schema_summary = {
        "FamilyCard_fields": sorted(FAMILY_FIELDS),
        "FeatureSpec_fields": sorted(SPEC_FIELDS),
        "parameter_set_fields": sorted(PARAMETER_FIELDS),
        "output_fields": sorted(OUTPUT_FIELDS),
        "output_count": "8..25",
    }
    rules = [
        "Return one strict JSON object and no markdown or prose.",
        "Never request or use training rows, targets, test labels, or exact scores.",
        "Use only controller-supplied citation IDs.",
        "Do not pad with arbitrary powers, bins, or parameter changes.",
        "Ideas are unverified until controller compilation and execution.",
    ]
    if role.get("class") == "family_architect":
        rules.append("At least one FamilyCard must declare target_affinity=both.")
        if role.get("specialty") == "cross-domain-invention":
            rules.append(
                "Exactly two FamilyCards must require kernel=custom; the third must use a trusted kernel."
            )
        else:
            rules.append("All three FamilyCards must use trusted kernels, not custom code.")
    if role.get("class") == "spec_builder":
        rules.append(
            f"Both spec_slug values must start with {role['id']}- and their output counts "
            "must each contain the 19 controller-assigned, physically justified scalars."
        )
    if role.get("class") == "plugin_writer":
        rules.append(
            "compute_family must return the union of assigned FeatureSpec output names "
            "as 8..25 finite scalar keys and honor every assigned configuration."
        )
    if role.get("class") in {"target_exploiter", "cross_family_synthesizer"}:
        rules.append(
            f"Return exactly two specs whose spec_slug values start with {role['id']}-; "
            "their output counts must total at least 48 physically justified scalars."
        )
    payload = {
        "role": role,
        "contract": contract,
        "rules": rules,
        "schema": schema_summary,
        "evidence": evidence,
        "atlas_novelty": novelty_summary,
        "controller_context": controller_context or {},
    }
    return _ensure_limit(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def build_retry_prompt(
    role: dict[str, Any], invalid_output: str, schema_errors: list[str]
) -> str:
    if len(invalid_output.encode("utf-8")) > OUTPUT_LIMIT_BYTES:
        raise PromptLimitError("invalid artifact exceeds the output ceiling")
    payload = {
        "role_id": role["id"],
        "role_class": role["class"],
        "instruction": "Correct the listed errors and return one complete strict JSON replacement.",
        "schema_errors": [str(error)[:512] for error in schema_errors[:50]],
        "invalid_artifact": invalid_output,
    }
    prompt = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if len(prompt.encode("utf-8")) > PROMPT_LIMIT_BYTES:
        payload["invalid_artifact"] = invalid_output.encode("utf-8")[:8192].decode(
            "utf-8", errors="ignore"
        )
        payload["artifact_truncated_for_prompt_limit"] = True
        prompt = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if len(prompt.encode("utf-8")) > PROMPT_LIMIT_BYTES:
        payload["schema_errors"] = payload["schema_errors"][:10]
        payload["invalid_artifact"] = str(payload["invalid_artifact"])[:4096]
        prompt = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return _ensure_limit(prompt)
