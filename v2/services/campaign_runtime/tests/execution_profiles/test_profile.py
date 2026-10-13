"""Owner-scoped compiler/profile/history policy; public fixture bytes only."""
import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
from amphora_campaign_runtime.compiler import ResolvedTool, ToolCatalog, SchemaCatalog, compile_campaign, CompilationError
from amphora_campaign_runtime.coordinator.configuration import load_materials
from amphora_campaign_runtime.definitions.validation import ValidationUniverse
from amphora_campaign_runtime.definitions.admission import DraftAdmissionGuard
from amphora_campaign_runtime.execution_profiles import StructuralExecutionProfile
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import Scope
from amphora_contracts_tools import LockEntry, ReleaseDescriptor

HERE=Path(__file__).parent

def canonical(data):
    return json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()

def locked(descriptor):
    return LockEntry.model_validate_json(json.dumps({"tool":descriptor.tool.binding.model_dump(),
        "descriptor_sha256":hashlib.sha256(canonical({"profile":"amphora-tool-release-v1","descriptor":descriptor.model_dump(mode="json")})).hexdigest(),
        "input_schemas":[{"port":p.name,"schema_ref":p.schema_ref.model_dump()} for p in descriptor.tool.inputs],
        "output_schemas":[{"port":p.name,"schema_ref":p.schema_ref.model_dump()} for p in descriptor.tool.outputs],
        "checkpoint_schema":descriptor.tool.checkpoint_schema}))

def materials():
    descriptor=ReleaseDescriptor.model_validate_json((HERE/'chemical-descriptor.json').read_bytes())
    definition=parse_executable_campaign((HERE/'chemical-graph.json').read_bytes())
    pins=json.loads((HERE.parents[1]/'src/amphora_campaign_runtime/execution_profiles/reviewed.json').read_bytes())
    profile=StructuralExecutionProfile.from_record({"profile":"supplied-finite-structure-v1","scope":definition.scope.model_dump(),
        "release":locked(descriptor).model_dump(mode="json"),"semantic_profile":pins['semantic_profile'],"context":"supplied-finite-molecules"})
    entry={"definition":"chemical-graph.json","releases":[{"descriptor":"chemical-descriptor.json","lock":profile.release.model_dump(mode="json"),"execution_profile":profile.record()}],
        "schemas":[{"schema_ref":pins[k],"path":"chemical-"+k+'.json'} for k in ('input','output')]}
    return descriptor,definition,profile,entry

def test_default_denied_explicit_profile_compiles_and_restores():
    descriptor,definition,profile,entry=materials()
    with pytest.raises(CompilationError,match='unsupported_compiler_tool_profile'):
        ResolvedTool(descriptor,profile.release)
    tools,schemas=load_materials(entry,HERE)
    plan=compile_campaign(definition,ToolCatalog(tools),SchemaCatalog(schemas))
    universe=ValidationUniverse(definition.scope,tools,schemas)
    assert universe.profile=='amphora-authoring-universe-v2'
    restored=ValidationUniverse.restore(universe.record(),universe.sha256)
    assert restored.record()==universe.record()
    assert compile_campaign(definition,ToolCatalog(restored.releases),SchemaCatalog(restored.schemas))==plan
    assert tools[0].execution_profile.context=='supplied-finite-molecules'
    for key in ('scope','release','semantic_profile','context','profile'):
        invalid=copy.deepcopy(universe.record())
        grant=invalid['tools'][0]['execution_profile']
        if key=='scope': grant[key]['project_id']='foreign'
        elif key=='release': grant[key]['tool']['image_sha256']='d'*64
        elif key=='semantic_profile': grant[key]['sha256']='d'*64
        else: grant[key]='wrong'
        with pytest.raises((ValueError,CompilationError)): ValidationUniverse.restore(invalid,universe.sha256)
    invalid=copy.deepcopy(universe.record());invalid['profile']='amphora-authoring-universe-v1'
    with pytest.raises(ValueError): ValidationUniverse.restore(invalid,universe.sha256)

@pytest.mark.parametrize('change',[{'authority_ceiling':'synthetic_only'}, {'egress':{'mode':'allowlist','hosts':['example.org']}}, {'tool':{'side_effects':'idempotent'}}])
def test_changed_descriptors_cannot_borrow_a_grant(change):
    descriptor,_,profile,_=materials()
    raw=descriptor.model_dump(mode='json')
    for key,value in change.items():
        if key=='tool': raw[key].update(value)
        else: raw[key]=value
    # Invalid public metadata also fails closed; no claim/compile is attempted.
    with pytest.raises((ValueError,CompilationError)):
        changed=ReleaseDescriptor.model_validate_json(json.dumps(raw))
        ResolvedTool(changed,locked(changed),profile)

@pytest.mark.parametrize('field',['capability_id','release','contract_version','image_sha256'])
def test_release_pin_mismatch(field):
    _,_,profile,_=materials();record=profile.record()
    record['release']['tool'][field]='d'*64 if field=='image_sha256' else 'wrong'
    with pytest.raises((ValueError,CompilationError)):
        altered=StructuralExecutionProfile.from_record(record)
        descriptor=ReleaseDescriptor.model_validate_json((HERE/'chemical-descriptor.json').read_bytes())
        ResolvedTool(descriptor,altered.release,altered)

def test_scope_and_current_grant_are_separate_from_historical_restore():
    _,definition,profile,entry=materials();tools,schemas=load_materials(entry,HERE)
    universe=ValidationUniverse(definition.scope,tools,schemas)
    foreign=Scope(tenant_id='foreign',project_id='foreign')
    with pytest.raises(ValueError,match='scope_mismatch'): ValidationUniverse(foreign,tools,schemas)
    raw=definition.model_dump(mode='json');raw['scope']=foreign.model_dump()
    with pytest.raises(CompilationError,match='scope_mismatch'):
        compile_campaign(parse_executable_campaign(json.dumps(raw)),ToolCatalog(tools),SchemaCatalog(schemas))
    restored=ValidationUniverse.restore(universe.record(),universe.sha256)
    guard=DraftAdmissionGuard(None,{})
    guard.material=NS(load=lambda *_: NS(universe=restored,require_selection=lambda *_: None))
    with pytest.raises(TransitionError,match='draft_universe_changed'):
        guard.prepare(definition.scope,NS(draft=NS(validation_id='retained')))
    assert restored.record()==universe.record()

def test_synthetic_universe_keeps_original_document(compiler_env):
    universe=ValidationUniverse(Scope(tenant_id='test',project_id='legacy'),(compiler_env.tool,),tuple(compiler_env.schema_list))
    document={'profile':'amphora-authoring-universe-v1','compiler':'amphora-deterministic-compiler-v3',
        'scope':universe.scope.model_dump(mode='json'),'tools':[compiler_env.tool.lock.model_dump(mode='json')],
        'schemas':sorted((s.identity.record() for s in universe.schemas),key=canonical)}
    assert universe.sha256==hashlib.sha256(canonical(document)).hexdigest()
    assert 'execution_profile' not in universe.record()['tools'][0]
    assert ValidationUniverse.restore(universe.record(),universe.sha256).record()==universe.record()


def test_structural_draft_requests_exact_context_and_mapping_reason(monkeypatch):
    from amphora_campaign_runtime.definitions.eligibility import RegistryEligibility
    from amphora_campaign_runtime.definitions.eligibility.observations import EligibilityUnavailable
    from ..definitions.test_eligibility import candidate
    descriptor,definition,profile,_=materials();tool=ResolvedTool(descriptor,profile.release,profile)
    verified=NS(universe=NS(releases=(tool,)),draft=NS(content=NS(definition=definition)),
        entry=NS(plan=NS(document=NS(lock=NS(tools=(tool.lock,))))))
    peer=RegistryEligibility('http://127.0.0.1:1','x'*32,'selector')
    original=candidate(tool,definition.scope)
    raw=json.loads(original.model_dump_json())
    raw['decision']['observations']['scientific']['reason_codes']=['supplied_structure_mapping_only']
    observed=[]
    def resolve(command,timeout):
        from amphora_contracts_tools import RegistryReceipt
        observed.append(json.loads(command.canonical_bytes)['payload'])
        return RegistryReceipt.model_validate_json(json.dumps(raw))
    monkeypatch.setattr(peer,'_resolve',resolve)
    assert len(peer.observe(verified))==1
    assert observed[0]['context']=='supplied-finite-molecules'
    monkeypatch.setattr(peer,'_resolve',lambda *_: original)
    with pytest.raises(EligibilityUnavailable): peer.observe(verified)
