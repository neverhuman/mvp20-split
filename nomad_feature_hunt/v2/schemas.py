from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

from .constants import (
    CUSTOM_PLUGIN_OUTPUTS,
    DOMAIN_KERNELS,
    DOMAIN_IDS,
    MAX_SPEC_OUTPUTS,
    MIN_SPEC_OUTPUTS,
    OUTPUT_LIMIT_BYTES,
    TARGETS,
    TRUSTED_KERNELS,
)


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FEATURE_ID_RE = re.compile(
    r"^v2\.d(?:0[1-9]|10)\.[a-z0-9]+(?:-[a-z0-9]+)*\."
    r"[a-z0-9]+(?:-[a-z0-9]+)*\.[a-z0-9]+(?:-[a-z0-9]+)*$"
)
INVARIANCES = {
    "translation",
    "rotation",
    "atom_permutation",
    "periodic_wrapping",
    "equivalent_cell",
}
TARGET_AFFINITIES = set(TARGETS) | {"both", "none"}

FAMILY_FIELDS = {
    "family_slug",
    "domain",
    "physical_hypothesis",
    "target_affinity",
    "kernel",
    "custom_plugin_required",
    "inputs",
    "citation_ids",
    "atlas_novelty_argument",
    "invariances",
    "falsifier",
    "complexity",
}
SPEC_FIELDS = {
    "spec_slug",
    "family_slug",
    "domain",
    "kernel",
    "parameter_sets",
    "aggregations",
    "outputs",
    "missingness_policy",
}
OUTPUT_FIELDS = {
    "name",
    "operation",
    "parameter_set",
    "aggregation",
    "equation",
    "unit",
    "physical_interpretation",
}
PARAMETER_FIELDS = {"id", "values", "physical_justification"}


class SchemaError(ValueError):
    def __init__(self, errors: Iterable[str]):
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def parse_strict_json(text: str, *, max_bytes: int = OUTPUT_LIMIT_BYTES) -> Any:
    """Parse one complete JSON value without markdown or nested-object salvage."""

    size = len(text.encode("utf-8"))
    if size > max_bytes:
        raise SchemaError([f"output is {size} bytes; limit is {max_bytes}"])
    stripped = text.strip()
    if not stripped:
        raise SchemaError(["output must contain one JSON value"])
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as error:
        raise SchemaError(
            [f"strict JSON error at line {error.lineno} column {error.colno}: {error.msg}"]
        ) from error


def _object_errors(value: Any, fields: set[str], name: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{name} must be an object"]
    errors = [f"{name} missing field: {field}" for field in sorted(fields - set(value))]
    errors.extend(f"{name} has unknown field: {field}" for field in sorted(set(value) - fields))
    return errors


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_family_card(value: Any, *, citation_ids: set[str] | None = None) -> list[str]:
    errors = _object_errors(value, FAMILY_FIELDS, "family card")
    if not isinstance(value, dict):
        return errors
    if not SLUG_RE.fullmatch(str(value.get("family_slug", ""))):
        errors.append("family_slug must be a lowercase kebab-case slug")
    if value.get("domain") not in DOMAIN_IDS:
        errors.append("domain must be D01..D10")
    for field in (
        "physical_hypothesis",
        "atlas_novelty_argument",
        "falsifier",
        "complexity",
    ):
        if not _nonempty_string(value.get(field)):
            errors.append(f"{field} must be a nonempty string")
    affinity = value.get("target_affinity")
    if isinstance(affinity, list):
        if not affinity or not set(affinity).issubset(set(TARGETS)):
            errors.append("target_affinity list contains an unsupported target")
    elif affinity not in TARGET_AFFINITIES:
        errors.append("target_affinity must be a target, both, none, or a target list")
    custom = value.get("custom_plugin_required")
    if not isinstance(custom, bool):
        errors.append("custom_plugin_required must be boolean")
    kernel = value.get("kernel")
    if custom is False and kernel not in TRUSTED_KERNELS:
        errors.append("non-custom families must name a trusted kernel")
    if custom is False and kernel in TRUSTED_KERNELS and kernel != DOMAIN_KERNELS.get(
        str(value.get("domain"))
    ):
        errors.append("trusted kernel must match the assigned physical domain")
    if custom is True and kernel != "custom":
        errors.append("custom families must use kernel=custom")
    for field in ("inputs", "citation_ids", "invariances"):
        item = value.get(field)
        if not isinstance(item, list) or not item or not all(_nonempty_string(v) for v in item):
            errors.append(f"{field} must be a nonempty string list")
    invariances = value.get("invariances", [])
    if isinstance(invariances, list) and set(invariances) != INVARIANCES:
        errors.append("all five required invariances must be declared exactly once")
    citations = value.get("citation_ids", [])
    if citation_ids is not None and isinstance(citations, list):
        unresolved = sorted(set(citations) - citation_ids)
        if unresolved:
            errors.append(f"unresolved citation IDs: {unresolved}")
    forbidden_inputs = {
        "target",
        "targets",
        "label",
        "labels",
        "test_label",
        "formation_energy_ev_natom",
        "bandgap_energy_ev",
    }
    if isinstance(value.get("inputs"), list):
        found = forbidden_inputs & {str(item).casefold() for item in value["inputs"]}
        if found:
            errors.append(f"forbidden target or label inputs: {sorted(found)}")
    return errors


def validate_feature_spec(
    value: Any, *, families: dict[str, dict[str, Any]] | None = None
) -> list[str]:
    errors = _object_errors(value, SPEC_FIELDS, "feature spec")
    if not isinstance(value, dict):
        return errors
    for field in ("spec_slug", "family_slug"):
        if not SLUG_RE.fullmatch(str(value.get(field, ""))):
            errors.append(f"{field} must be a lowercase kebab-case slug")
    if value.get("domain") not in DOMAIN_IDS:
        errors.append("domain must be D01..D10")
    if value.get("kernel") not in set(TRUSTED_KERNELS) | {"custom"}:
        errors.append("kernel is unsupported")
    family = None
    if families is not None:
        family = families.get(str(value.get("family_slug"))) or families.get(
            f"{value.get('domain')}:{value.get('family_slug')}"
        )
    if families is not None and family is None:
        errors.append("family_slug does not resolve to a FamilyCard")
    elif family is not None:
        if family.get("domain") != value.get("domain"):
            errors.append("spec domain differs from its FamilyCard")
        if family.get("kernel") != value.get("kernel"):
            errors.append("spec kernel differs from its FamilyCard")

    parameter_sets = value.get("parameter_sets")
    parameter_ids: set[str] = set()
    if not isinstance(parameter_sets, list) or not parameter_sets:
        errors.append("parameter_sets must be a nonempty list")
    else:
        for index, parameter_set in enumerate(parameter_sets):
            nested = _object_errors(parameter_set, PARAMETER_FIELDS, f"parameter_sets[{index}]")
            errors.extend(nested)
            if not isinstance(parameter_set, dict):
                continue
            identifier = parameter_set.get("id")
            if not SLUG_RE.fullmatch(str(identifier or "")):
                errors.append(f"parameter_sets[{index}].id must be a slug")
            elif identifier in parameter_ids:
                errors.append(f"duplicate parameter set ID: {identifier}")
            else:
                parameter_ids.add(str(identifier))
            if not isinstance(parameter_set.get("values"), dict):
                errors.append(f"parameter_sets[{index}].values must be an object")
            elif value.get("kernel") in TRUSTED_KERNELS:
                from .kernels import validate_kernel_config

                errors.extend(
                    f"parameter_sets[{index}]: {error}"
                    for error in validate_kernel_config(
                        str(value.get("kernel")), parameter_set["values"]
                    )
                )
            if not _nonempty_string(parameter_set.get("physical_justification")):
                errors.append(
                    f"parameter_sets[{index}].physical_justification must be nonempty"
                )

    aggregations = value.get("aggregations")
    aggregation_ids = {
        item for item in aggregations if isinstance(item, str)
    } if isinstance(aggregations, list) else set()
    if (
        not isinstance(aggregations, list)
        or not aggregations
        or not all(SLUG_RE.fullmatch(str(item)) for item in aggregations)
        or len(aggregation_ids) != len(aggregations)
    ):
        errors.append("aggregations must be a unique nonempty list of slugs")

    outputs = value.get("outputs")
    if not isinstance(outputs, list) or not MIN_SPEC_OUTPUTS <= len(outputs) <= MAX_SPEC_OUTPUTS:
        errors.append(f"outputs must contain {MIN_SPEC_OUTPUTS}..{MAX_SPEC_OUTPUTS} scalars")
    else:
        names: set[str] = set()
        for index, output in enumerate(outputs):
            errors.extend(_object_errors(output, OUTPUT_FIELDS, f"outputs[{index}]"))
            if not isinstance(output, dict):
                continue
            name = output.get("name")
            if not SLUG_RE.fullmatch(str(name or "")):
                errors.append(f"outputs[{index}].name must be a slug")
            elif name in names:
                errors.append(f"duplicate output name: {name}")
            else:
                names.add(str(name))
            if not SLUG_RE.fullmatch(str(output.get("operation", ""))):
                errors.append(f"outputs[{index}].operation must be a slug")
            elif value.get("kernel") in TRUSTED_KERNELS:
                from .kernels import KERNEL_OPERATIONS

                if output.get("operation") not in KERNEL_OPERATIONS[str(value["kernel"])]:
                    errors.append(
                        f"outputs[{index}] uses an unsupported trusted-kernel operation"
                    )
            elif value.get("kernel") == "custom" and (
                output.get("name") not in CUSTOM_PLUGIN_OUTPUTS
                or output.get("operation") != output.get("name")
            ):
                errors.append(
                    f"outputs[{index}] must use a controller-approved custom output name"
                )
            parameter_set = output.get("parameter_set")
            if not isinstance(parameter_set, str) or parameter_set not in parameter_ids:
                errors.append(f"outputs[{index}] references an unknown parameter set")
            aggregation = output.get("aggregation")
            if not isinstance(aggregation, str) or aggregation not in aggregation_ids:
                errors.append(f"outputs[{index}] references an unknown aggregation")
            for field in ("equation", "unit", "physical_interpretation"):
                if not _nonempty_string(output.get(field)):
                    errors.append(f"outputs[{index}].{field} must be nonempty")
    if not _nonempty_string(value.get("missingness_policy")):
        errors.append("missingness_policy must be a nonempty string")
    return errors


def controller_feature_id(domain: str, family: str, spec: str, output: str) -> str:
    candidate = f"v2.{domain.casefold()}.{family}.{spec}.{output}"
    if not FEATURE_ID_RE.fullmatch(candidate):
        raise SchemaError([f"invalid controller feature ID components: {candidate}"])
    return candidate


def formula_fingerprint(
    equation: str,
    *,
    configuration: dict[str, Any] | None = None,
    operation: str = "",
    aggregation: str = "",
) -> str:
    normalized = equation.casefold().replace("−", "-").replace("×", "*")
    normalized = re.sub(r"\s+", "", normalized)
    normalized = re.sub(r"(?<![a-z_])[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?", "#", normalized)
    payload = {
        "equation": normalized,
        "configuration": configuration,
        "operation": operation,
        "aggregation": aggregation,
    }
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def semantic_fingerprint(*values: str) -> str:
    tokens = set()
    for value in values:
        tokens.update(re.findall(r"[a-z][a-z0-9]+", value.casefold()))
    tokens -= {"the", "and", "for", "with", "from", "that", "this", "into", "per"}
    return hashlib.sha256(" ".join(sorted(tokens)).encode()).hexdigest()


def expand_feature_spec(
    card: dict[str, Any], spec: dict[str, Any], *, source_role_id: str = "controller"
) -> list[dict[str, Any]]:
    family_errors = validate_family_card(card)
    spec_errors = validate_feature_spec(spec, families={str(card.get("family_slug")): card})
    if family_errors or spec_errors:
        raise SchemaError(family_errors + spec_errors)
    parameters = {item["id"]: item for item in spec["parameter_sets"]}
    rows: list[dict[str, Any]] = []
    for output in spec["outputs"]:
        feature_id = controller_feature_id(
            spec["domain"], spec["family_slug"], spec["spec_slug"], output["name"]
        )
        parameter_set = parameters[output["parameter_set"]]
        rows.append(
            {
                "feature_id": feature_id,
                "campaign_version": "2",
                "domain": spec["domain"],
                "family_slug": spec["family_slug"],
                "spec_slug": spec["spec_slug"],
                "base_equation_id": (
                    f"v2.{spec['domain'].casefold()}.{spec['family_slug']}.{spec['spec_slug']}"
                ),
                "output_name": output["name"],
                "operation": output["operation"],
                "kernel": spec["kernel"],
                "configuration": parameter_set["values"],
                "parameter_justification": parameter_set["physical_justification"],
                "aggregation": output["aggregation"],
                "equation": output["equation"],
                "unit": output["unit"],
                "normalization": output["aggregation"],
                "inputs": card["inputs"],
                "periodic_construction": "controller-owned canonical periodic structure",
                "invariances": card["invariances"],
                "missingness_policy": spec["missingness_policy"],
                "physical_interpretation": output["physical_interpretation"],
                "physical_hypothesis": card["physical_hypothesis"],
                "target_affinity": card["target_affinity"],
                "citation_ids": card["citation_ids"],
                "atlas_novelty_argument": card["atlas_novelty_argument"],
                "falsifier": card["falsifier"],
                "complexity": card["complexity"],
                "source_role_id": source_role_id,
                "formula_fingerprint": formula_fingerprint(
                    output["equation"],
                    configuration=parameter_set["values"],
                    operation=output["operation"],
                    aggregation=output["aggregation"],
                ),
                "semantic_fingerprint": semantic_fingerprint(
                    card["physical_hypothesis"],
                    output["physical_interpretation"],
                    card["falsifier"],
                    output["operation"],
                    json.dumps(parameter_set["values"], sort_keys=True),
                    output["aggregation"],
                ),
                "status": "uncomputed",
            }
        )
    return rows


def validate_role_payload(
    role: dict[str, Any],
    payload: Any,
    *,
    families: dict[str, dict[str, Any]] | None = None,
    citation_ids: set[str] | None = None,
    available_receipt_ids: set[str] | None = None,
) -> list[str]:
    if not isinstance(payload, dict):
        return ["role payload must be an object"]
    role_class = role.get("class")
    errors: list[str] = []
    if role_class == "evidence_curator":
        if set(payload) != {"sources", "atlas_gaps"}:
            errors.append("evidence curator payload must contain only sources and atlas_gaps")
        if not isinstance(payload.get("sources"), list) or not payload.get("sources"):
            errors.append("sources must be a nonempty list")
        if not isinstance(payload.get("atlas_gaps"), list) or not payload.get("atlas_gaps"):
            errors.append("atlas_gaps must be a nonempty list")
    elif role_class == "family_architect":
        cards = payload.get("family_cards")
        if set(payload) != {"family_cards"} or not isinstance(cards, list) or len(cards) != 3:
            return ["family architect must return exactly three family_cards"]
        for index, card in enumerate(cards):
            errors.extend(
                f"family_cards[{index}]: {error}"
                for error in validate_family_card(card, citation_ids=citation_ids)
            )
            if isinstance(card, dict) and card.get("domain") != role.get("domain"):
                errors.append(f"family_cards[{index}] is outside the assigned domain")
        custom_count = sum(
            isinstance(card, dict) and card.get("custom_plugin_required") is True
            for card in cards
        )
        expected_custom = 2 if role.get("specialty") == "cross-domain-invention" else 0
        if custom_count != expected_custom:
            errors.append(
                f"{role.get('specialty')} architect must return exactly "
                f"{expected_custom} custom-plugin FamilyCards"
            )
        if not any(
            isinstance(card, dict)
            and (
                card.get("target_affinity") == "both"
                or set(card.get("target_affinity", [])) == set(TARGETS)
                if isinstance(card.get("target_affinity"), list)
                else card.get("target_affinity") == "both"
            )
            for card in cards
        ):
            errors.append("family architect must return at least one both-target FamilyCard")
    elif role_class == "spec_builder":
        specs = payload.get("feature_specs")
        if set(payload) != {"feature_specs"} or not isinstance(specs, list) or len(specs) != 2:
            return ["spec builder must return exactly two feature_specs"]
        for index, spec in enumerate(specs):
            errors.extend(
                f"feature_specs[{index}]: {error}"
                for error in validate_feature_spec(spec, families=families)
            )
            if isinstance(spec, dict) and spec.get("domain") != role.get("domain"):
                errors.append(f"feature_specs[{index}] is outside the assigned domain")
            if isinstance(spec, dict) and not str(spec.get("spec_slug", "")).startswith(
                f"{role.get('id')}-"
            ):
                errors.append(f"feature_specs[{index}].spec_slug must be role-prefixed")
        if any(
            len(spec.get("outputs", [])) != 19 for spec in specs if isinstance(spec, dict)
        ):
            errors.append("each spec builder FeatureSpec must contain exactly 19 scalars")
    elif role_class == "plugin_writer":
        allowed = {"family_slug", "plugin_source", "adversarial_tests"}
        if set(payload) != allowed:
            errors.append(f"plugin writer payload fields must be {sorted(allowed)}")
        if not _nonempty_string(payload.get("family_slug")):
            errors.append("family_slug must be nonempty")
        family = (
            families.get(str(payload.get("family_slug"))) if families is not None else None
        )
        if families is not None and family is None:
            errors.append("plugin family_slug does not resolve to a FamilyCard")
        elif family is not None and family.get("custom_plugin_required") is not True:
            errors.append("plugin writers may only implement custom-plugin FamilyCards")
        if not _nonempty_string(payload.get("plugin_source")):
            errors.append("plugin_source must be nonempty")
        if not isinstance(payload.get("adversarial_tests"), list) or not payload.get(
            "adversarial_tests"
        ):
            errors.append("adversarial_tests must be a nonempty list")
    elif role_class in {"target_exploiter", "cross_family_synthesizer"}:
        specs = payload.get("feature_specs")
        if set(payload) != {"feature_specs"} or not isinstance(specs, list) or len(specs) != 2:
            return ["adaptive role must return exactly two feature_specs"]
        for index, spec in enumerate(specs):
            errors.extend(
                f"feature_specs[{index}]: {error}"
                for error in validate_feature_spec(spec, families=families)
            )
            if isinstance(spec, dict) and not str(spec.get("spec_slug", "")).startswith(
                f"{role.get('id')}-"
            ):
                errors.append(f"feature_specs[{index}].spec_slug must be role-prefixed")
        if sum(len(spec.get("outputs", [])) for spec in specs if isinstance(spec, dict)) < 48:
            errors.append("adaptive role outputs must total at least 48 executable scalars")
    elif role_class in {"experimental_analyst", "blind_judge"}:
        field = "analysis" if role_class == "experimental_analyst" else "judgments"
        required = {field, "matrix_receipt_ids", "score_receipt_ids"}
        if set(payload) != required:
            errors.append(f"{role_class} payload fields must be {sorted(required)}")
        if not isinstance(payload.get(field), list) or not payload.get(field):
            errors.append(f"{field} must be a nonempty list")
        receipt_ids = list(payload.get("matrix_receipt_ids") or []) + list(
            payload.get("score_receipt_ids") or []
        )
        if not receipt_ids or not all(_nonempty_string(value) for value in receipt_ids):
            errors.append("matrix and score receipt IDs must be nonempty string lists")
        if available_receipt_ids is not None:
            missing = sorted(set(receipt_ids) - available_receipt_ids)
            if missing:
                errors.append(f"unknown matrix or score receipt IDs: {missing}")
    elif role_class == "memory_curator":
        required = {"classifications", "receipt_ids"}
        if set(payload) != required:
            errors.append("memory curator payload must contain classifications and receipt_ids")
        if not isinstance(payload.get("classifications"), list):
            errors.append("classifications must be a list")
        receipts = payload.get("receipt_ids")
        if not isinstance(receipts, list) or not all(_nonempty_string(item) for item in receipts):
            errors.append("receipt_ids must be a string list")
        if available_receipt_ids is not None and isinstance(receipts, list):
            missing = sorted(set(receipts) - available_receipt_ids)
            if missing:
                errors.append(f"unknown receipt IDs: {missing}")
        forbidden = {"feature_specs", "family_cards", "targets", "target_rows"} & set(payload)
        if forbidden:
            errors.append(f"memory curator may not invent feature inputs: {sorted(forbidden)}")
    else:
        errors.append(f"unsupported role class: {role_class}")
    return errors
