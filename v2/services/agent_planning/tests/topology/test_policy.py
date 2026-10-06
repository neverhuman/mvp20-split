import copy
import importlib.util
import json
from pathlib import Path
import pytest
from amphora_agent_planning.topology import TopologyPolicyState, TopologyProposal
from amphora_contracts_campaigns import ExecutionPlanV4
from amphora_contracts_topology_search import TopologyPolicy

spec=importlib.util.spec_from_file_location('topology_vectors',Path(__file__).with_name('fixtures.py'))
F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)


def test_swap_changes_only_requested_release_and_revision():
    state=F.bind(*F.fixture());before=state.plan().document.definition.model_dump(mode='json')
    result=TopologyProposal.decide(state,F.request(state)).to_wire()
    expected=copy.deepcopy(before);expected['revision']=2
    expected['body']['nodes'][0]['tool']=state.policy().allowed_edits[0].replacement.tool.model_dump(mode='json')
    assert result.status=='proposed' and result.definition.model_dump(mode='json')==expected
    assert state.plan().document.definition.model_dump(mode='json')==before
    assert result.authority=='proposal_only' and result.scientific_authority=='not_established'
    assert TopologyProposal.decide(state,F.request(state)).to_wire()==result


def test_insert_preserves_downstream_binding_and_reroutes_only_selected_input():
    state=F.bind(*F.fixture());result=TopologyProposal.decide(state,F.request(state,'insert')).to_wire()
    assert result.status=='proposed'
    body=result.definition.model_dump(mode='json')['body']
    assert [n['node_id'] for n in body['nodes']]==['transform','evaluate','done']
    assert body['nodes'][0]['inputs']==[{'port':'parameters','source':{'kind':'input','name':'parameters'}}]
    assert body['nodes'][1]['inputs']==[{'port':'parameters','source':{'kind':'output','node_id':'transform','port':'result'}}]
    assert body['nodes'][2]==state.plan().document.definition.model_dump(mode='json')['body']['nodes'][1]
    assert body['edges']==[{'source':'evaluate','target':'done','route':'next'},{'source':'transform','target':'evaluate','route':'next'}]


def test_inactive_original_may_be_replaced_but_not_used_as_new_tool():
    plan,policy,releases=F.fixture();releases[0]['status']='revoked'
    state=F.bind(plan,policy,releases)
    assert TopologyProposal.decide(state,F.request(state)).to_wire().status=='proposed'
    releases[1]['status']='draining';state=F.bind(plan,policy,releases)
    assert TopologyProposal.decide(state,F.request(state)).to_wire().reasons==('topology_release_inactive',)


@pytest.mark.parametrize('case,code',[
 ('unit','topology_port_mismatch'),('schema','topology_port_mismatch'),('representation','topology_port_mismatch'),
 ('input-name','topology_port_mismatch'),('checkpoint','topology_checkpoint_mismatch'),('timeout','topology_timeout'),
 ('resource','topology_resource_increase'),('capability','topology_evaluator_identity'),('authority','topology_release_authority')],ids=lambda x:x)
def test_incompatible_evaluator_preserves_rejected_proposal(case,code):
    plan,policy,releases=F.fixture();new=releases[1];d=new['descriptor'];tool=d['tool']
    if case=='unit':tool['outputs'][0]['unit']='kg'
    elif case=='schema':tool['outputs'][0]['schema_ref']=dict(F.SCHEMA,sha256='9'*64)
    elif case=='representation':tool['outputs'][0]['representation']='foreign'
    elif case=='input-name':tool['inputs'][0]['name']='foreign'
    elif case=='checkpoint':tool['checkpoint_schema']=F.SCHEMA
    elif case=='timeout':d['resources']['timeout_seconds']=1
    elif case=='resource':d['resources']['memory_mib']=512
    elif case=='capability':tool['binding']['capability_id']='different'
    else:tool['side_effects']='idempotent'
    F.relock(new);policy['allowed_edits'][0]['replacement']=new['lock']
    state=F.bind(plan,policy,releases);result=TopologyProposal.decide(state,F.request(state)).to_wire()
    assert result.status=='rejected' and result.definition is None and result.reasons==(code,)
    assert result.request.edit_id=='swap' and result.policy==state.policy()


@pytest.mark.parametrize('case,code',[
 ('duplicate','topology_insert_duplicate'),('source','topology_source_changed'),('input','topology_input_unknown'),
 ('unary','topology_transform_unary'),('port','topology_transform_port'),('unit','topology_port_mismatch'),
 ('timeout','topology_timeout'),('control','topology_insert_control_join')],ids=lambda x:x)
def test_transform_failures_are_retained_without_mutation(case,code):
    plan,policy,releases=F.fixture();edit=policy['allowed_edits'][1];d=releases[2]['descriptor']
    if case=='duplicate':edit['node_id']='done'
    elif case=='source':edit['expected_source']={'kind':'input','name':'other'}
    elif case=='input':edit['target_input']='other'
    elif case=='unary':d['tool']['inputs'].append(dict(d['tool']['inputs'][0],name='extra'))
    elif case=='port':edit['transform_output']='other'
    elif case=='unit':d['tool']['outputs'][0]['unit']='kg'
    elif case=='timeout':edit['timeout_seconds']=61
    else:plan['document']['definition']['body']['edges'] += [{'source':'one','target':'evaluate','route':'next'},{'source':'two','target':'evaluate','route':'next'}]
    F.relock(releases[2]);edit['transform']=releases[2]['lock'];state=F.bind(plan,policy,releases)
    value=TopologyProposal.decide(state,F.request(state,'insert')).to_wire()
    assert value.status=='rejected' and value.reasons==(code,)


@pytest.mark.parametrize('edit,revision,code',[('missing',2,'topology_edit_not_allowed'),('swap',1,'topology_successor_revision'),('swap',3,'topology_successor_revision')])
def test_unknown_edit_and_revision_do_not_compile(edit,revision,code):
    state=F.bind(*F.fixture());result=TopologyProposal.decide(state,F.request(state,edit,successor_revision=revision)).to_wire()
    assert result.reasons==(code,)


def test_forged_parent_and_policy_identity_reject_before_proposal():
    state=F.bind(*F.fixture());plan=state.plan().model_dump(mode='json');plan['sha256']='f'*64
    with pytest.raises(ValueError,match='topology_parent_digest'):
        TopologyPolicyState.bind(state.policy(),ExecutionPlanV4.model_validate_json(json.dumps(plan)),state.releases())
    with pytest.raises(ValueError,match='topology_request_binding'):
        TopologyProposal.decide(state,F.request(state,scope={'tenant_id':'foreign','project_id':'policy'}))
    wrong=dict(state.reference.model_dump(mode='json'),sha256='e'*64)
    with pytest.raises(ValueError,match='topology_request_binding'):TopologyProposal.decide(state,F.request(state,policy=wrong))
    value=json.loads(TopologyProposal.decide(state,F.request(state)).canonical);value['status']='rejected'
    with pytest.raises(ValueError,match='topology_projection_digest'):TopologyProposal(json.dumps(value).encode()).to_wire()


def test_duplicate_policy_edits_reject_as_configuration_error():
    plan,policy,releases=F.fixture();policy['allowed_edits'].append(copy.deepcopy(policy['allowed_edits'][0]))
    with pytest.raises(ValueError,match='topology_duplicate_edit'):F.bind(plan,policy,releases)


def test_nested_scope_edit_and_missing_scope_rejection():
    plan,policy,releases=F.fixture();inner=copy.deepcopy(plan['document']['definition']['body'])
    group={'kind':'scatter','node_id':'group','collection':{'kind':'input','name':'parameters'},'item_input':'parameters','captures':[],
           'max_members':1,'max_parallel':1,'body':inner,'result_port':'result',
           'output':{'name':'result','value_type':{'kind':'collection','item':F.SHAPE,'max_items':1,'missing_slots':False}},
           'policy':{'kind':'all','skipped':'exclude'}}
    body=plan['document']['definition']['body'];body['nodes'][0]=group;body['edges'][0]['source']='group'
    body['nodes'][1]['outputs'][0]['source']['node_id']='group'
    policy['allowed_edits'][0]['target']['scope_path']=['group']
    state=F.bind(plan,policy,releases);result=TopologyProposal.decide(state,F.request(state)).to_wire()
    assert result.status=='proposed'
    assert result.definition.body.nodes[0].body.nodes[0].tool==state.policy().allowed_edits[0].replacement.tool
    policy['allowed_edits'][0]['target']['scope_path']=['absent'];state=F.bind(plan,policy,releases)
    assert TopologyProposal.decide(state,F.request(state)).to_wire().reasons==('topology_scope_unknown',)


def test_insert_redirects_existing_control_edge_without_changing_route():
    plan,policy,releases=F.fixture();body=plan['document']['definition']['body']
    first=copy.deepcopy(body['nodes'][0]);first['node_id']='prepare';body['nodes'].insert(0,first)
    body['edges'].insert(0,{'source':'prepare','target':'evaluate','route':'next'})
    state=F.bind(plan,policy,releases);result=TopologyProposal.decide(state,F.request(state,'insert')).to_wire()
    edges=result.definition.model_dump(mode='json')['body']['edges']
    assert edges[0]=={'source':'prepare','target':'transform','route':'next'}
    assert edges[-1]=={'source':'transform','target':'evaluate','route':'next'}


def test_insert_cannot_exceed_public_local_node_limit():
    plan,policy,releases=F.fixture();body=plan['document']['definition']['body']
    for i in range(254):
        node=copy.deepcopy(body['nodes'][0]);node['node_id']='fixture-'+str(i);body['nodes'].insert(0,node)
    state=F.bind(plan,policy,releases)
    value=TopologyProposal.decide(state,F.request(state,'insert')).to_wire()
    assert value.status=='rejected' and value.reasons==('topology_result_shape',)


def test_binding_fails_for_different_cut_and_duplicate_carry_targets():
    state=F.bind(*F.fixture())
    with pytest.raises(ValueError,match='topology_predecessor_binding'):
        TopologyProposal.decide(state,F.request(state,predecessor={'run_id':'previous','plan_sha256':'f'*64,'revision':5}))
    carry={'target_port':'parameters','source':{'kind':'run_output','port':'result'},'expected_value_sha256':'c'*64}
    with pytest.raises(ValueError,match='topology_duplicate_carry'):
        TopologyProposal.decide(state,F.request(state,carried=[carry,carry]))


def test_omitted_release_and_noninvoke_target_reject():
    plan,policy,releases=F.fixture();state=F.bind(plan,policy,releases[:1])
    assert TopologyProposal.decide(state,F.request(state)).to_wire().reasons==('topology_release_lock',)
    policy['allowed_edits'][0]['target']['node_id']='done';state=F.bind(plan,policy,releases)
    assert TopologyProposal.decide(state,F.request(state)).to_wire().reasons==('topology_target_not_invocation',)
