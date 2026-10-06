"""Declared public metadata for pure policy tests, never authenticated owner evidence."""
import copy
import hashlib
import json
from amphora_contracts_campaigns import ExecutionPlanV4
from amphora_contracts_tools import ReleaseSnapshot
from amphora_contracts_topology_search import TopologyPolicy, TopologyRequest
from amphora_agent_planning.topology import TopologyPolicyState

SCOPE={'tenant_id':'topology','project_id':'policy'}
SCHEMA={'schema_id':'fixture.number','version':'1','sha256':'1'*64}
SHAPE={'kind':'artifact','schema_ref':SCHEMA,'representation':'fixture.number','unit':'1','media_type':'application/json'}


def hash_of(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def release(name='fixture.evaluate',version='1.0.0'):
    tool={'schema_version':'1','binding':{'capability_id':name,'release':version,'image_sha256':hash_of([name,version]),'contract_version':'1'},
          'purpose':'Synthetic topology metadata fixture','applicability':['synthetic-tests'],
          'inputs':[{'name':'parameters','schema_ref':SCHEMA,'representation':'fixture.number','unit':'1','required':True}],
          'outputs':[{'name':'result','schema_ref':SCHEMA,'representation':'fixture.number','unit':'1','required':True}],
          'side_effects':'pure','checkpoint_schema':None}
    descriptor={'schema_version':'1','tool':tool,'resources':{'architectures':['x86_64'],'operating_systems':['linux'],
         'cpu_millicores':1000,'memory_mib':256,'gpu_count':0,'timeout_seconds':60,'max_parallel_invocations':1,'max_batch_size':1},
         'egress':{'mode':'deny'},'checkpoint':{'mode':'none','readable_schema_sha256':[]},'reproducibility':'deterministic',
         'authority_ceiling':'synthetic_only','examples':['Pure synthetic scalar transformation'],'anti_examples':['No scientific validity claim']}
    return relock({'scope':SCOPE,'descriptor':descriptor,'revision':2,'status':'active'})


def relock(record):
    descriptor=record['descriptor'];tool=descriptor['tool']
    record['lock']={'schema_version':'1','tool':copy.deepcopy(tool['binding']),
        'descriptor_sha256':hash_of({'profile':'amphora-tool-release-v1','descriptor':descriptor}),
        'input_schemas':[{'port':p['name'],'schema_ref':p['schema_ref']} for p in tool['inputs']],
        'output_schemas':[{'port':p['name'],'schema_ref':p['schema_ref']} for p in tool['outputs']],
        'checkpoint_schema':tool['checkpoint_schema']}
    return record


def fixture():
    old,new,transform=release(),release(version='2.0.0'),release('fixture.transform')
    definition={'schema_version':'4','profile':'deterministic-v3','campaign_id':'search','revision':1,'scope':SCOPE,'context':[],
        'body':{'inputs':[{'name':'parameters','value_type':SHAPE}],'outputs':[{'name':'result','value_type':SHAPE}],
            'nodes':[{'kind':'invoke','node_id':'evaluate','tool':old['lock']['tool'],'inputs':[{'port':'parameters','source':{'kind':'input','name':'parameters'}}],
                      'checkpoint':None,'timeout_seconds':30},
                     {'kind':'finish','node_id':'done','outputs':[{'port':'result','source':{'kind':'output','node_id':'evaluate','port':'result'}}]}],
            'edges':[{'source':'evaluate','target':'done','route':'next'}]}}
    lock={'schema_version':'4','compiler_profile':'amphora-deterministic-compiler-v3','definition_sha256':'0'*64,
          'tools':[old['lock']],'schemas':[SCHEMA],'context':[]}
    plan={'schema_version':'4','sha256':'0'*64,'document':{'profile':'amphora-execution-plan-v3','definition':definition,'lock':lock,
        'scopes':[{'path':[],'order':['evaluate','done'],'nodes':[{'node_id':'evaluate','inputs':definition['body']['inputs'],'outputs':definition['body']['outputs']},
                  {'node_id':'done','inputs':[],'outputs':definition['body']['outputs']}]}]}}
    edits=[{'kind':'evaluator_swap','edit_id':'swap','target':{'scope_path':[],'node_id':'evaluate'},'expected_tool':old['lock']['tool'],'replacement':new['lock']},
        {'kind':'transform_insertion','edit_id':'insert','target':{'scope_path':[],'node_id':'evaluate'},'target_input':'parameters',
         'expected_source':{'kind':'input','name':'parameters'},'node_id':'transform','transform':transform['lock'],
         'transform_input':'parameters','transform_output':'result','timeout_seconds':30}]
    policy={'wire_version':'1','authority':'synthetic_proposal_policy','parent':{'scope':SCOPE,'plan_sha256':'0'*64,'definition_sha256':'0'*64},
            'allowed_edits':edits,'evaluator_call_limit':6}
    return plan,policy,[old,new,transform]


def bind(plan,policy,releases):
    plan=ExecutionPlanV4.model_validate_json(json.dumps(plan)).model_dump(mode='json')
    definition=plan['document']['definition'];lock=plan['document']['lock']
    lock['definition_sha256']=hash_of({'profile':'amphora-executable-definition-v4','definition':definition})
    plan['sha256']=hash_of(plan['document'])
    policy['parent'].update(plan_sha256=plan['sha256'],definition_sha256=lock['definition_sha256'])
    return TopologyPolicyState.bind(TopologyPolicy.model_validate_json(json.dumps(policy)),ExecutionPlanV4.model_validate_json(json.dumps(plan)),
        tuple(ReleaseSnapshot.model_validate_json(json.dumps(r)) for r in releases))


def request(state,edit='swap',**changes):
    value={'scope':SCOPE,'proposal_id':'trial','policy':state.reference.model_dump(mode='json'),
        'predecessor':{'run_id':'previous','plan_sha256':state.plan().sha256,'revision':5},'edit_id':edit,'successor_revision':2,'carried':[]}
    value.update(changes)
    return TopologyRequest.model_validate_json(json.dumps(value))
