from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .constants import DOMAINS, MAX_COLUMNS_PER_BASE_EQUATION


DOMAIN_IDS = {domain.id for domain in DOMAINS}
CONCEPT_FIELDS = {
    "concept_id",
    "domain",
    "name",
    "equation",
    "symbols",
    "inputs",
    "parameters",
    "units",
    "normalization",
    "periodic_construction",
    "invariances",
    "missingness_policy",
    "physical_interpretation",
    "citations_or_derivation",
    "target_hypothesis",
    "complexity",
    "leakage_assessment",
    "falsification_test",
    "microfeature_expansion",
    "implementation_guidance",
}
MICROFEATURE_FIELDS = {
    "feature_id",
    "concept_id",
    "domain",
    "base_equation_id",
    "equation",
    "symbols",
    "inputs",
    "parameters",
    "units",
    "normalization",
    "periodic_construction",
    "invariances",
    "missingness_policy",
    "physical_interpretation",
    "citations_or_derivation",
    "target_hypothesis",
    "complexity",
    "generator_hash",
    "leakage_assessment",
    "falsification_test",
    "measured_results",
}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,127}$")


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def validate_concept(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["concept must be an object"]
    errors = [f"missing or empty field: {field}" for field in sorted(CONCEPT_FIELDS) if not _nonempty(value.get(field))]
    if value.get("domain") not in DOMAIN_IDS:
        errors.append("domain must be one of D01..D10")
    if not ID_RE.fullmatch(str(value.get("concept_id", ""))):
        errors.append("concept_id has an invalid format")
    expansion = value.get("microfeature_expansion")
    if not isinstance(expansion, list) or not expansion:
        errors.append("microfeature_expansion must be a nonempty list")
    return errors


def validate_microfeature(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["microfeature must be an object"]
    errors = [f"missing or empty field: {field}" for field in sorted(MICROFEATURE_FIELDS) if not _nonempty(value.get(field))]
    if value.get("domain") not in DOMAIN_IDS:
        errors.append("domain must be one of D01..D10")
    for field in ("feature_id", "concept_id", "base_equation_id"):
        if not ID_RE.fullmatch(str(value.get(field, ""))):
            errors.append(f"{field} has an invalid format")
    generator_hash = str(value.get("generator_hash", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", generator_hash):
        errors.append("generator_hash must be a lowercase SHA-256")
    return errors


def validate_base_equation_cap(features: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for feature in features:
        equation_id = str(feature.get("base_equation_id", ""))
        counts[equation_id] = counts.get(equation_id, 0) + 1
    return [
        f"base equation {equation_id} expands to {count} columns (limit {MAX_COLUMNS_PER_BASE_EQUATION})"
        for equation_id, count in sorted(counts.items())
        if count > MAX_COLUMNS_PER_BASE_EQUATION
    ]


def _normalize_formula(formula: str) -> str:
    normalized = formula.casefold().replace("−", "-").replace("×", "*")
    normalized = re.sub(r"\s+", "", normalized)
    normalized = re.sub(r"(?<![A-Za-z_])[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?", "#", normalized)
    return normalized


def formula_fingerprint(feature: dict[str, Any]) -> str:
    payload = {
        "equation": _normalize_formula(str(feature.get("equation", ""))),
        "normalization": _normalize_formula(str(feature.get("normalization", ""))),
        "periodic": _normalize_formula(str(feature.get("periodic_construction", ""))),
        "inputs": sorted(map(str, feature.get("inputs", []))),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def semantic_tokens(feature: dict[str, Any]) -> frozenset[str]:
    fields = (
        "physical_interpretation",
        "target_hypothesis",
        "falsification_test",
        "periodic_construction",
    )
    tokens: set[str] = set()
    for field in fields:
        tokens.update(re.findall(r"[a-z][a-z0-9]+", str(feature.get(field, "")).casefold()))
    stop = {"the", "and", "for", "with", "from", "that", "this", "into", "over", "per"}
    return frozenset(tokens - stop)


def semantic_fingerprint(feature: dict[str, Any]) -> str:
    return hashlib.sha256(" ".join(sorted(semantic_tokens(feature))).encode()).hexdigest()


def semantic_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_tokens = semantic_tokens(left)
    right_tokens = semantic_tokens(right)
    union = left_tokens | right_tokens
    if not union:
        return 1.0
    return len(left_tokens & right_tokens) / len(union)


def extract_json_payload(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        starts = [index for index, char in enumerate(stripped) if char in "[{"]
        for start in starts:
            try:
                value, _end = decoder.raw_decode(stripped[start:])
                return value
            except json.JSONDecodeError:
                continue
        raise ValueError("assistant output contains no parseable JSON payload")


def validate_role_payload(role_class: str, payload: Any, domain: str) -> list[str]:
    if not isinstance(payload, dict):
        return ["role payload must be an object"]
    errors: list[str] = []
    if role_class in {"literature_scout", "theorist"}:
        concepts = payload.get("concepts")
        if not isinstance(concepts, list) or not concepts:
            return ["role payload must include a nonempty concepts list"]
        minimum = 12 if role_class == "literature_scout" else 20
        if len(concepts) < minimum:
            errors.append(f"{role_class} must return at least {minimum} concepts")
        for index, concept in enumerate(concepts):
            for error in validate_concept(concept):
                errors.append(f"concept[{index}]: {error}")
            if domain != "ALL" and isinstance(concept, dict) and concept.get("domain") != domain:
                errors.append(f"concept[{index}] is outside assigned domain {domain}")
    elif role_class == "feature_implementer":
        code = payload.get("generator_code")
        features = payload.get("microfeatures")
        if not isinstance(code, str) or not code.strip():
            errors.append("implementer payload needs nonempty generator_code")
        if not isinstance(features, list) or len(features) < 150:
            errors.append("implementer must attempt at least 150 microfeatures")
        else:
            for index, feature in enumerate(features):
                for error in validate_microfeature(feature):
                    errors.append(f"microfeature[{index}]: {error}")
                if domain != "ALL" and isinstance(feature, dict) and feature.get("domain") != domain:
                    errors.append(f"microfeature[{index}] is outside assigned domain {domain}")
            errors.extend(validate_base_equation_cap(features))
    elif role_class == "experimental_analyst":
        if not isinstance(payload.get("analysis"), list) or not payload["analysis"]:
            errors.append("analyst payload needs a nonempty analysis list")
    elif role_class == "blind_judge":
        if not isinstance(payload.get("judgments"), list) or not payload["judgments"]:
            errors.append("judge payload needs a nonempty judgments list")
    elif role_class == "memory_curator":
        if not isinstance(payload.get("memory_items"), list):
            errors.append("curator payload needs a memory_items list")
    else:
        errors.append(f"unsupported role class: {role_class}")
    return errors
