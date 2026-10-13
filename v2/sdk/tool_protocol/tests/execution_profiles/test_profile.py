"""Opt-in configuration rejects before claim; lifecycle tests own actual lease policy."""
import json
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
from amphora_contracts_core import Scope
from amphora_contracts_tools import ReleaseDescriptor
from amphora_tool_protocol import PureToolWorker, ProtocolError, StructuralExecutionProfile, WorkerIdentity, WorkerConfig
HERE=Path(__file__).parent

def inputs():
    descriptor=ReleaseDescriptor.model_validate_json((HERE/'descriptor.json').read_bytes())
    record=json.loads((HERE/'grant.json').read_bytes())
    return descriptor,Scope.model_validate(record['scope']),record

class Runtime:
    def __init__(self,scope): self.identity=WorkerIdentity('worker',scope);self.claims=0
    def claim(self,*_,**__): self.claims+=1;return NS(outcome=NS(status='no_eligible_work'))

def test_default_rejects_explicit_profile_claims_only_its_scope():
    descriptor,scope,record=inputs();runtime=Runtime(scope);artifact=NS(identity=runtime.identity)
    with pytest.raises(ProtocolError): PureToolWorker(runtime,artifact,descriptor,lambda b:b)
    assert runtime.claims==0
    worker=PureToolWorker(runtime,artifact,descriptor,lambda b:b,execution_profile=StructuralExecutionProfile.from_record(record))
    assert worker.run_once('run')=={'status':'no_eligible_work'} and runtime.claims==1
    foreign=Runtime(Scope(tenant_id='other',project_id='other'))
    with pytest.raises(ProtocolError): PureToolWorker(foreign,NS(identity=foreign.identity),descriptor,lambda b:b,execution_profile=StructuralExecutionProfile.from_record(record))
    assert foreign.claims==0

@pytest.mark.parametrize('change',['scope','image','descriptor','input','output','semantic','context','profile','extra'])
def test_invalid_config_never_claims(change):
    descriptor,scope,record=inputs();runtime=Runtime(scope)
    if change=='scope':record['scope']['project_id']='foreign'
    elif change=='image':record['release']['tool']['image_sha256']='d'*64
    elif change=='descriptor':record['release']['descriptor_sha256']='d'*64
    elif change in ('input','output'):record['release'][change+'_schemas'][0]['schema_ref']['sha256']='d'*64
    elif change=='semantic':record['semantic_profile']['sha256']='d'*64
    elif change=='extra':record['extra']=True
    else:record[change]='wrong'
    with pytest.raises((ValueError,ProtocolError)):
        PureToolWorker(runtime,NS(identity=runtime.identity),descriptor,lambda b:b,execution_profile=StructuralExecutionProfile.from_record(record))
    assert runtime.claims==0

def test_config_boundary_requires_full_grant_and_preserves_default():
    _,scope,record=inputs()
    config={'actor_id':'worker','scope':scope.model_dump(),'run_id':'run','image_sha256':'c'*64,
            'runtime':{'endpoint':'http://127.0.0.1:1','token_env':'TOKEN'},'artifacts':{'endpoint':'http://127.0.0.1:2','token_env':'TOKEN'}}
    assert WorkerConfig.model_validate_json(json.dumps(config)).execution_profile is None
    config['execution_profile']=record
    assert WorkerConfig.model_validate_json(json.dumps(config)).execution_profile.to_domain().record()==record
    config['execution_profile']=True
    with pytest.raises(ValueError):WorkerConfig.model_validate_json(json.dumps(config))
