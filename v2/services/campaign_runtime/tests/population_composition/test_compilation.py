import copy
import json
import pytest

from amphora_campaign_runtime.compiler import CompilationError, compile_campaign
from amphora_contracts_campaigns import parse_executable_campaign

from .catalog import CompositionCatalog
from .definition import campaign, process_campaign, WIDTHS


def compile_raw(raw, catalog):
    return compile_campaign(parse_executable_campaign(json.dumps(raw)), catalog.resolved, catalog.schemas)


@pytest.mark.parametrize("batch", [1, 8, 32])
def test_nested_population_batches_and_parallel_methods_compile(batch):
    catalog = CompositionCatalog(batch)
    raw = campaign(catalog, batch=batch)
    plan = compile_raw(raw, catalog)
    assert plan.sha256 == compile_raw(copy.deepcopy(raw), catalog).sha256
    assert len(plan.document.scopes) == 4
    loop = raw["body"]["nodes"][1]
    batches = loop["body"]["nodes"][0]
    candidate = batches["body"]["nodes"][2]["body"]
    assert loop["max_iterations"] == 4
    assert batches["max_iterations"] == (12 + batch - 1) // batch
    assert not any(e["source"] == "evaluate_a" and e["target"] == "evaluate_b" for e in candidate["edges"])
    assert candidate["nodes"][3]["policy"]["close"] == "all_terminal"
    assert {e["source"] for e in candidate["edges"] if e["target"] == "evaluate_b"} == {"prepare_b"}


def test_nineteen_stages_widen_and_converge_through_actual_multi_input_tools():
    catalog = CompositionCatalog(8)
    raw = process_campaign(catalog)
    plan = compile_raw(raw, catalog)
    assert len(plan.document.scopes) == 1
    assert len(raw["body"]["nodes"]) == sum(WIDTHS) + 1
    combine = next(n for n in raw["body"]["nodes"] if n["node_id"] == "stage_5_0")
    assert len(combine["inputs"]) == 4
    assert {i["source"]["node_id"] for i in combine["inputs"]} == {f"stage_4_{i}" for i in range(4)}


@pytest.mark.parametrize("fault", ["missing_input", "wrong_slice_bound", "cycle"])
def test_invalid_composition_is_rejected(fault):
    catalog = CompositionCatalog(8)
    raw = campaign(catalog)
    batches = raw["body"]["nodes"][1]["body"]["nodes"][0]["body"]
    if fault == "missing_input":
        batches["nodes"][2]["body"]["nodes"][0]["inputs"] = []
    elif fault == "wrong_slice_bound":
        batches["nodes"][1]["output"]["value_type"]["max_items"] = 7
    else:
        batches["edges"].append({"source": "collect", "target": "slice", "route": "next"})
    with pytest.raises(CompilationError):
        compile_raw(raw, catalog)
