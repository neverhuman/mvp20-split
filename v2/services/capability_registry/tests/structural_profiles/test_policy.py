import copy
import json
from pathlib import Path
from dataclasses import replace
from datetime import datetime, UTC, timedelta
import pytest
from amphora_contracts_core import Scope, SchemaRef
from amphora_contracts_tools import ReleaseDescriptor
from amphora_capability_registry.structural_profiles import StructuralGrant, StructuralPolicy
from amphora_capability_registry.descriptors.identity import ReleaseDocument
from amphora_capability_registry.descriptors.policy import EvaluationPolicy, PermissionPolicy, EligibilityEvaluator
from amphora_capability_registry.descriptors.requirements import ResourceAllowance, CapabilityNeed
from amphora_capability_registry.descriptors.assessments import CapacityObservation
from amphora_capability_registry.hosting import HostConfig
from importlib.resources import files

NOW=datetime(2026,10,13,tzinfo=UTC)
SCOPE=Scope(tenant_id="internal",project_id="structure-tests")

def setup(scope=SCOPE):
    descriptor=ReleaseDescriptor.model_validate_json(Path(__file__).with_name("descriptor.json").read_bytes())
    pins=json.loads(files("amphora_capability_registry.structural_profiles").joinpath("reviewed.json").read_bytes())
    lock=ReleaseDocument.from_descriptor(descriptor).to_lock()
    grant=StructuralGrant(scope,lock,SchemaRef.model_validate(pins["semantic_profile"]))
    return descriptor,grant

def evaluate(descriptor,structural,scope=SCOPE,context="supplied-finite-molecules",capacity="available"):
    policy=EvaluationPolicy(scope,ResourceAllowance("x86_64","linux",2000,1024,0,300,8,128),PermissionPolicy(),structural)
    need=CapabilityNeed.for_tool(scope,context,descriptor.tool)
    observation=CapacityObservation(scope,ReleaseDocument.from_descriptor(descriptor).digest,0 if capacity=="unavailable" else 1,1 if capacity in ("available","stale") else 0,NOW-timedelta(seconds=2),NOW-timedelta(seconds=1) if capacity=="stale" else NOW+timedelta(seconds=30))
    return EligibilityEvaluator().evaluate(descriptor,need,policy,observation,now=NOW).to_wire()

def test_default_denied_exact_grant_permits_bounded_structural_task():
    descriptor,grant=setup()
    assert not StructuralPolicy().can_activate(SCOPE,descriptor)
    assert evaluate(descriptor,StructuralPolicy()).status=="rejected"
    policy=StructuralPolicy((grant,))
    assert policy.can_activate(SCOPE,descriptor)
    result=evaluate(descriptor,policy)
    assert result.status=="candidate"
    assert result.observations.scientific.reason_codes==("supplied_structure_mapping_only",)

@pytest.mark.parametrize("fault",["scope","context","descriptor","image","release","input","output","side-effect","egress","applicability"])
def test_exact_bindings_and_authority_cannot_be_widened(fault):
    descriptor,grant=setup(); raw=descriptor.model_dump(mode="json"); scope=SCOPE; context="supplied-finite-molecules"
    if fault=="scope": scope=Scope(tenant_id="other",project_id="structure-tests")
    elif fault=="context": context="drug-efficacy"
    elif fault=="descriptor": raw["tool"]["purpose"]="other purpose"
    elif fault=="image": raw["tool"]["binding"]["image_sha256"]="f"*64
    elif fault=="release": raw["tool"]["binding"]["release"]="0.2.0"
    elif fault in ("input","output"): raw["tool"][fault+"s"][0]["schema_ref"]["sha256"]="f"*64
    elif fault=="side-effect": raw["tool"]["side_effects"]="idempotent"
    elif fault=="egress": raw["egress"]={"mode":"allowlist","hosts":["example.com"]}
    else: raw["tool"]["applicability"]=["drug-efficacy"]
    changed=ReleaseDescriptor.model_validate_json(json.dumps(raw))
    policy=StructuralPolicy((grant,))
    if fault!="context": assert not policy.can_activate(scope,changed)
    assert evaluate(changed,policy,scope,context).status=="rejected"

@pytest.mark.parametrize("fault",["profile","profile-id","context","input","release"])
def test_bad_grant_configuration_rejected(fault):
    _,grant=setup()
    with pytest.raises(ValueError):
        if fault=="profile": replace(grant,semantic_profile=grant.semantic_profile.model_copy(update={"sha256":"f"*64}))
        elif fault=="profile-id": replace(grant,semantic_profile=grant.semantic_profile.model_copy(update={"schema_id":"other"}))
        elif fault=="context": replace(grant,context="other")
        elif fault=="input": replace(grant,release=grant.release.model_copy(update={"input_schemas":()}))
        else: replace(grant,release=grant.release.model_copy(update={"tool":grant.release.tool.model_copy(update={"release":"other"})}))

@pytest.mark.parametrize("capacity",["unavailable","busy","stale"])
def test_eligibility_never_replaces_capacity(capacity):
    descriptor,grant=setup()
    result=evaluate(descriptor,StructuralPolicy((grant,)),capacity=capacity)
    assert result.status=="rejected" and result.observations.scientific.status=="eligible"

def test_grant_order_deterministic_and_duplicates_rejected():
    _,a=setup(); b=replace(a,scope=Scope(tenant_id="another",project_id="p"))
    assert StructuralPolicy((a,b)).fingerprint("a"*64)==StructuralPolicy((b,a)).fingerprint("a"*64)
    with pytest.raises(ValueError): StructuralPolicy((a,a))


def test_legacy_policy_digest_matches_independent_registry_010():
    _,grant=setup()
    policy=EvaluationPolicy(SCOPE,ResourceAllowance("x86_64","linux",2000,1024,0,300,8,128),PermissionPolicy())
    assert policy.digest=="8c71fd5661b45c1e409b91414d2b7a00f7367f5ac1b7e9b4db96580e0dff980b"
    configured=replace(policy,structural=StructuralPolicy((grant,)))
    assert configured.digest==policy.digest
    assert configured.structural.fingerprint(policy.digest)!=policy.digest


def test_host_grants_decode_to_same_domain_policy():
    _,grant=setup()
    raw={"database_url_env":"DB","principals":[{"actor_id":"a","scope":SCOPE.model_dump(),"token_env":"TOKEN","actions":["read"]}],"resources":{"architecture":"x86_64","operating_system":"linux","cpu_millicores":2000,"memory_mib":1024,"gpu_count":0,"timeout_seconds":300,"max_parallel_invocations":8,"max_batch_size":128},"structural_profiles":[{"profile":"supplied-finite-structure-v1",**grant.record()}]}
    config=HostConfig.model_validate_json(json.dumps(raw))
    assert config.structural_profiles[0].to_domain()==grant
    raw["structural_profiles"][0]["profile"]="any-evidence"
    with pytest.raises(ValueError): HostConfig.model_validate_json(json.dumps(raw))
