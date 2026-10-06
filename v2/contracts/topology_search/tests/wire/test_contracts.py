import copy
import json
import pytest
from pydantic import ValidationError
from amphora_contracts_topology_search import TopologyPolicy, TopologyRequest, TopologyProjection

SCOPE={'tenant_id':'topology','project_id':'fixture'}
PIN={'schema_id':'fixture.topology','version':'1','sha256':'a'*64}
TOOL={'capability_id':'fixture.evaluate','release':'1.0.0','image_sha256':'b'*64,'contract_version':'1'}
LOCK={'tool':TOOL,'descriptor_sha256':'c'*64,'input_schemas':[{'port':'parameters','schema_ref':PIN}],
      'output_schemas':[{'port':'result','schema_ref':PIN}],'checkpoint_schema':None}
SWAP={'kind':'evaluator_swap','edit_id':'swap','target':{'scope_path':[],'node_id':'evaluate'},
      'expected_tool':dict(TOOL,release='0.9.0'),'replacement':LOCK}
INSERT={'kind':'transform_insertion','edit_id':'insert','target':{'scope_path':['generation'],'node_id':'evaluate'},
        'target_input':'parameters','expected_source':{'kind':'input','name':'candidate'},'node_id':'transform',
        'transform':LOCK,'transform_input':'parameters','transform_output':'result','timeout_seconds':30}
POLICY={'parent':{'scope':SCOPE,'plan_sha256':'d'*64,'definition_sha256':'e'*64},
        'allowed_edits':[SWAP,INSERT],'evaluator_call_limit':6}
REQUEST={'scope':SCOPE,'proposal_id':'successor','policy':PIN,'predecessor':{'run_id':'parent','plan_sha256':'d'*64,'revision':3},
         'edit_id':'swap','successor_revision':2,'carried':[]}


def parse(model,value):
    return model.model_validate_json(json.dumps(value))


def test_exact_transport_roundtrip_and_authority():
    policy=parse(TopologyPolicy,POLICY)
    request=parse(TopologyRequest,REQUEST)
    assert policy.allowed_edits[0].kind=='evaluator_swap'
    assert policy.allowed_edits[1].target.scope_path==('generation',)
    assert parse(TopologyPolicy,policy.model_dump(mode='json'))==policy
    assert parse(TopologyRequest,request.model_dump(mode='json'))==request
    projection=parse(TopologyProjection,{'reference':{'scope':SCOPE,'proposal_id':'successor','sha256':'f'*64},
        'request':REQUEST,'policy':POLICY,'status':'rejected','reasons':['incompatible_port'],'definition':None})
    assert projection.authority=='proposal_only' and projection.scientific_authority=='not_established'


@pytest.mark.parametrize('field,value',[
    ('authority','execution_grant'),('allowed_edits',[]),('allowed_edits',[SWAP]*65),
    ('evaluator_call_limit',0),('evaluator_call_limit',1000001),('evaluator_call_limit',True)
],ids=['authority','empty','edit-cap','zero-budget','budget-cap','boolean-budget'])
def test_closed_policy_limits(field,value):
    raw=copy.deepcopy(POLICY);raw[field]=value
    with pytest.raises(ValidationError):parse(TopologyPolicy,raw)


@pytest.mark.parametrize('change', ['kind','source','depth','timeout','release'],ids=['code-generation','extra-source','scope-depth','zero-timeout','missing-release-pin'])
def test_edits_cannot_bypass_named_shapes(change):
    raw=copy.deepcopy(POLICY)
    if change=='kind':raw['allowed_edits'][0]['kind']='generate_code'
    elif change=='source':raw['allowed_edits'][0]['source_code']='print(1)'
    elif change=='depth':raw['allowed_edits'][0]['target']['scope_path']=['nested']*17
    elif change=='timeout':raw['allowed_edits'][1]['timeout_seconds']=0
    else:del raw['allowed_edits'][0]['replacement']['descriptor_sha256']
    with pytest.raises(ValidationError):parse(TopologyPolicy,raw)


@pytest.mark.parametrize('field,value',[('edit_id',['swap','insert']),('successor_revision',0),('carried',[{'unexpected':'data'}]),('code','arbitrary')],ids=['single-edit','revision','carry-shape','no-code'])
def test_request_remains_bounded_selection(field,value):
    raw=copy.deepcopy(REQUEST);raw[field]=value
    with pytest.raises(ValidationError):parse(TopologyRequest,raw)
