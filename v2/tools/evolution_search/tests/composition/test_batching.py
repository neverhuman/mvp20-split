"""Authored batching preserves the primary method and uses real slice cursors."""
from pathlib import Path
import json

import pytest
from amphora_contracts_campaigns import ExecutableCampaignV4
from amphora_evolution_search.composition.batching import PrimaryBatchLoop
from amphora_evolution_search.composition import GraphWorkBounds


def method():
    return ExecutableCampaignV4.model_validate_json((Path(__file__).parents[1]/
        "population_workers/primary-method-definition.json").read_bytes())


@pytest.mark.parametrize("batch",[1,8,32])
def test_real_slice_cursor_controls_loop_without_changing_method(batch):
    frozen=method();before=frozen.model_dump_json()
    author=PrimaryBatchLoop(frozen,max_population=32,batch_size=batch,max_parallel=4,image_sha256="f"*64)
    loop=author.build(dict(kind="input",name="request"),prepared=dict(kind="input",name="prepared"))
    scatter=next(node for node in loop.body.nodes if node.node_id=="evaluate")
    assert scatter.body==frozen.body
    assert frozen.model_dump_json()==before
    assert loop.max_iterations==32//batch and loop.on_limit=="blocked"
    assert loop.until.left.source.name=="complete" and loop.until.right.value is True
    next_index=next(node for node in loop.body.nodes if node.node_id=="next_index")
    assert next_index.source.node_id=="slice" and next_index.path==("next_index",)
    graph=frozen.model_dump(mode="json")
    graph["body"]=dict(inputs=[dict(name="request",value_type=author.request_shape),dict(name="prepared",value_type=author.prepared_shape)],
        outputs=[dict(name="result",value_type=author.request_shape)],nodes=[loop.model_dump(mode="json"),
            dict(kind="finish",node_id="finish",outputs=[dict(port="result",source=dict(kind="output",node_id="batches",port="request"))])],
        edges=[dict(source="batches",target="finish",route="next")])
    work=GraphWorkBounds.from_definition(ExecutableCampaignV4.model_validate_json(json.dumps(graph))).work
    counts={binding.capability_id:count for binding,count in work.calls}
    assert counts["numeric.population-evaluate-squares"]==32*(32//batch)
    # Public slice schema retains max32; compiler cannot narrow it from request.limit.
    assert counts["numeric.population-slice"]==32//batch
    assert work.bindings.materializations==32//batch


@pytest.mark.parametrize("change",[{"batch_size":0},{"batch_size":33},{"max_parallel":9},
    {"max_population":0},{"batch_size":True}])
def test_invalid_operational_limits(change):
    arguments=dict(max_population=32,batch_size=8,max_parallel=4,image_sha256="f"*64)
    arguments.update(change)
    with pytest.raises(ValueError):PrimaryBatchLoop(method(),**arguments)
