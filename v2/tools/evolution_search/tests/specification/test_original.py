import json
from pathlib import Path

import pytest
from amphora_contracts_search import SearchSpec
from amphora_evolution_search import NumericBox, OriginalSearch


def original():
    return OriginalSearch(SearchSpec.model_validate_json(
        Path(__file__).with_name("synthetic_specification.json").read_bytes()))


def changed(search, path, value):
    data = search.record.model_dump(mode="json")
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return SearchSpec.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("path,value", [
    (("seed",), "f" * 64),
    (("variables", 0, "upper"), 2.0),
    (("objectives", 0, "direction"), "maximize"),
    (("objectives", 0, "unit"), "kg"),
    (("evaluator", "tool", "release"), "0.2.0"),
    (("evaluator", "constraints", "sha256"), "f" * 64),
    (("implementations", 0, "sha256"), "f" * 64),
    (("operators", "mutation_fraction"), 0.5),
    (("budget", "max_evaluations"), 99),
])
def test_changed_original_cannot_resume_even_with_recomputed_digest(path, value):
    bound = original()
    modified = OriginalSearch(changed(bound, path, value))
    with pytest.raises(ValueError, match="original_specification"):
        bound.require_binding(modified.record, modified.digest)


def test_round_trip_binding_and_objective_space():
    bound = original()
    bound.require_binding(bound.record, bound.digest)
    assert bound.objectives.directions == ("minimize",)
    assert bound.box.contains((0.5,))
    assert not bound.box.contains((True,))
    assert not bound.box.contains((0.5, 0.7))
    assert not bound.box.contains((float("nan"),))
    assert not bound.box.contains((1.5,))


@pytest.mark.parametrize("path,value,code", [
    (("variables", 0, "lower"), 2.0, "box_order"),
    (("objectives", 0, "unit"), " ", "blank_unit"),
    (("evaluator", "constraints", "scope", "tenant_id"), "other", "specification_scope"),
])
def test_structurally_valid_but_inconsistent_spec_rejects(path, value, code):
    with pytest.raises(ValueError, match=code):
        OriginalSearch(changed(original(), path, value))


@pytest.mark.parametrize("field,label", [("variables", "variable"), ("objectives", "objective"),
                                          ("implementations", "implementation")])
def test_duplicate_coordinate_or_implementation_identity(field, label):
    bound = original()
    items = bound.record.model_dump(mode="json")[field]
    with pytest.raises(ValueError, match="duplicate_" + label):
        OriginalSearch(changed(bound, (field,), items * 2))


def test_duplicate_artifact_identity():
    bound = original()
    artifact = bound.record.evaluator.constraints.model_dump(mode="json")
    with pytest.raises(ValueError, match="duplicate_context"):
        OriginalSearch(changed(bound, ("evaluator", "context"), [artifact]))


def test_sampling_consumes_fixed_axis_draw_and_stays_within_large_bounds():
    bound = original()
    box = NumericBox(((4.0, 4.0), (-1e100, 1e100)))
    genes, after = box.sample(bound.initial_random())
    assert genes[0] == 4.0
    assert box.contains(genes)
    assert after.counter == 2


@pytest.mark.parametrize("bounds", [(), ((0, 1.0),), ((0.0,),), ((0.0, float("inf")),),
                                    ((2.0, 1.0),), ((0.0, 1.0),) * 33])
def test_invalid_numeric_box(bounds):
    with pytest.raises(ValueError):
        NumericBox(bounds)
