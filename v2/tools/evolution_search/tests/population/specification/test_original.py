import copy
import json
from pathlib import Path

import pytest
from amphora_contracts_population import PopulationSpecification
from amphora_evolution_search.population import OriginalPopulation, canonical

FIXTURE = Path(__file__).parent / "fixtures/specification.json"


def original(document=None):
    return OriginalPopulation(PopulationSpecification.model_validate_json(
        json.dumps(document) if document is not None else FIXTURE.read_bytes()))


def test_original_is_independent_and_changed_pins_cannot_resume():
    first = original()
    first.require_binding(first.record, first.digest)
    for field in ("seed", "revision", "search_id"):
        document = json.loads(FIXTURE.read_bytes())
        document[field] = {"seed": "1" * 64, "revision": 2, "search_id": "other"}[field]
        other = original(document)
        with pytest.raises(ValueError, match="population_original_specification"):
            first.require_binding(other.record, other.digest)


@pytest.mark.parametrize("case,code", [
    ("variables", "variable_identity"), ("reversed", "variable_bounds"),
    ("unit", "objective_unit"), ("methods", "method_identity"), ("node", "method_node"),
    ("objectives", "objective_identity"), ("optional", "objective_method_optional"),
    ("unknown", "objective_method_unknown"), ("duplicate_dependency", "objective_method_duplicate"),
    ("implementation", "implementation_identity"), ("scope", "reference_scope"),
    ("conflict", "reference_conflict"), ("context", "context_duplicate"),
    ("knowledge", "knowledge_duplicate"), ("minimum", "minimum_parents"),
])
def test_semantic_invalidity_cannot_hide_behind_valid_dto(case, code):
    d = json.loads(FIXTURE.read_bytes())
    if case == "variables": d["variables"] *= 2
    if case == "reversed": d["variables"][0]["lower"] = 2.0
    if case == "unit": d["assembly"]["objectives"][0]["objective"]["unit"] = " "
    if case == "methods": d["method_graph"]["methods"][1]["method_id"] = "cost"
    if case == "node": d["method_graph"]["methods"][1]["node_path"] = ["evaluate", "cost"]
    if case == "objectives": d["assembly"]["objectives"] *= 2
    if case == "optional": d["method_graph"]["methods"][1]["required"] = False
    if case == "unknown": d["assembly"]["objectives"][0]["method_ids"] = ["unknown"]
    if case == "duplicate_dependency": d["assembly"]["objectives"][0]["method_ids"] = ["cost", "cost"]
    if case == "implementation": d["implementations"] *= 2
    if case == "scope": d["constraints"]["scope"]["project_id"] = "other"
    if case == "conflict":
        reference = copy.deepcopy(d["constraints"]); reference["sha256"] = "f" * 64
        d["context"] = [reference]
    if case == "context": d["context"] = [d["constraints"], d["constraints"]]
    if case == "knowledge": d["knowledge"] = [d["constraints"], d["constraints"]]
    if case == "minimum": d["budget"]["population_size"] = 1
    # The wire accepts the shape; behavior rejects the incompatible meanings.
    PopulationSpecification.model_validate_json(json.dumps(d))
    with pytest.raises(ValueError, match="population_" + code):
        original(d)


def test_single_parent_requires_explicit_policy_and_optional_annotations_are_allowed():
    d = json.loads(FIXTURE.read_bytes())
    d["budget"]["population_size"] = 1
    d["selection"]["minimum_parents"] = 1
    d["method_graph"]["methods"][1]["required"] = False
    d["assembly"]["objectives"][0]["method_ids"] = ["cost"]
    assert original(d).record.selection.minimum_parents == 1


def test_profile_bytes_include_defaults_and_have_no_newline():
    full = original()
    d = json.loads(FIXTURE.read_bytes())
    d["selection"] = {}
    assert canonical(original(d).record) == canonical(full.record)
    assert not canonical(full.record).endswith(b"\n")


def test_exact_canonical_golden_and_independent_dotnet_hash():
    # .NET SHA256 over the documented ASCII prefix + zero + stored canonical bytes.
    value = original()
    assert canonical(value.record) == (FIXTURE.parent / "canonical.json").read_bytes()
    assert value.digest == "eb4f5f4d33ab921a4d55f9c61c839af3c9ce85aec839096e99d7746a7d255587"
