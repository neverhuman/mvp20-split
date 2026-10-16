"""Synthetic transform semantics and pre-publication bounds, no acceptance claim."""
from types import SimpleNamespace

import pytest
from amphora_contracts_population import (AbsentProcessInput,MaterialState,MaterialUse,
    ProcessBinding,ProcessPort,population_record_schema)
from amphora_contracts_tools import ToolBinding
from amphora_process_mapping import canonical
from amphora_process_mapping.payloads import TransformMaterialsRequest,ProposedProcessTransform,schema_ref
from amphora_process_mapping.transform import TransformPreparation,UNKNOWNS

from ..mapping.test_publication import case


def transform_case(factory,*,outputs=2,optional=False):
    context,schema,conditions,artifact,_=factory
    _,session,client=case(factory)
    tool=ToolBinding(capability_id="process.synthetic-transform-materials",release="0.3.0",
        image_sha256="f"*64,contract_version="1")
    binding=ProcessBinding(tool=tool,inputs=(ProcessPort(port="precursors",required=True,representation=schema,maximum=32),
        *((ProcessPort(port="annotation",required=False,representation=schema,maximum=1),) if optional else ())),
        outputs=(ProcessPort(port="products",required=True,representation=schema,maximum=32),))
    names=("left-0","left-1","right-0")
    materials=[]
    for name in names:
        record=MaterialState.model_validate_json(client.contents[name])
        materials.append(artifact(name,population_record_schema("population.material-state"),record))
    request=TransformMaterialsRequest(schema_version="1",profile="synthetic-transform-materials-v1",
        policy="copy-first-representation-v1",context=context,binding=binding,
        inputs=tuple(MaterialUse(port="precursors",ordinal=i,material=m.reference) for i,m in enumerate(materials)),
        absent=(AbsentProcessInput(port="annotation",reason_code="not_available"),) if optional else (),
        conditions=conditions,output_count=outputs)
    carrier=artifact("transform-request",schema_ref(TransformMaterialsRequest,"process-worker.transform-request"),request)
    client.contents[carrier.reference.artifact_id]=carrier.content
    invocation=session.attempt.invocation
    invocation.inputs=(SimpleNamespace(port="parameters",artifact=carrier.reference),)
    invocation.tool=tool;invocation.activation_id="d"*64
    session.release=tool.release
    return request,carrier,session,client


def test_many_inputs_produce_fresh_states_and_no_inferred_physical_properties(material_factory):
    request,carrier,session,client=transform_case(material_factory)
    prepared=TransformPreparation.load(request,session)
    assert len(prepared.inputs)==3 and len(prepared.states)==2
    assert len({state.state_id for state in prepared.states})==2
    for state in prepared.states:
        assert state.context==request.context and state.revision==1
        assert state.amount is state.composition is state.phase is state.material_batch_id is None
        assert state.unknowns==UNKNOWNS and state.conditions==request.conditions
        assert state.representation==prepared.inputs[0].record.representation
    root=prepared.publish(session,carrier.reference)
    result=root.decode(ProposedProcessTransform,schema_ref(ProposedProcessTransform,"process-worker.transform-result"),session.scope)
    assert result.request==carrier.reference and len(result.outputs)==2
    assert result.source.activation_id==session.attempt.invocation.activation_id
    assert "completion_id" not in result.source.model_dump()
    assert len(client.uploads)==3
    for use in result.outputs:
        parents=client.declarations[use.material.artifact_id].inputs
        assert carrier.reference in parents
        assert {value.material for value in request.inputs}<={ref for ref in parents}


def test_retry_preserves_state_identity_but_other_occurrences_are_distinct(material_factory):
    request,_,session,_=transform_case(material_factory)
    first=TransformPreparation.load(request,session).states
    session.attempt.invocation.attempt_id="retry"
    assert TransformPreparation.load(request,session).states==first
    session.attempt.invocation.activation_id="e"*64
    assert {state.state_id for state in TransformPreparation.load(request,session).states}.isdisjoint(
        state.state_id for state in first)


def test_explicit_optional_absence_is_preserved(material_factory):
    request,_,session,_=transform_case(material_factory,optional=True)
    assert TransformPreparation.load(request,session).request.absent==request.absent
    with pytest.raises(ValueError,match="optional_absence"):
        TransformPreparation.load(request.model_copy(update={"absent":()}),session)


@pytest.mark.parametrize("damage,reason",[("context","context"),("role","port_order"),
    ("representation","representation"),("envelope","envelope"),("tool","binding")])
def test_invalid_transform_rejects_before_child_publication(material_factory,damage,reason):
    request,carrier,session,client=transform_case(material_factory,outputs=32 if damage=="envelope" else 2)
    if damage=="context":request=request.model_copy(update={"context":request.context.model_copy(update={"process_batch_id":"another"})})
    if damage=="role":request=request.model_copy(update={"inputs":tuple(reversed(request.inputs))})
    if damage=="representation":
        output=request.binding.outputs[0].model_copy(update={"representation":request.binding.outputs[0].representation.model_copy(update={"sha256":"e"*64})})
        request=request.model_copy(update={"binding":request.binding.model_copy(update={"outputs":(output,)})})
    if damage=="tool":request=request.model_copy(update={"binding":request.binding.model_copy(update={"tool":request.binding.tool.model_copy(update={"release":"9.0.0"})})})
    with pytest.raises(ValueError,match=reason):TransformPreparation.load(request,session).publish(session,carrier.reference)
    assert client.uploads=={}
