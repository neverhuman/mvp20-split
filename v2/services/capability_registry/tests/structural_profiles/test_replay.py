import json
from pathlib import Path
from importlib.resources import files
import pytest
from amphora_contracts_core import SchemaRef
from amphora_contracts_tools import parse_registry_command
from amphora_contracts_tools import ReleaseDescriptor
from amphora_capability_registry.structural_profiles import StructuralGrant, StructuralPolicy
from amphora_capability_registry.catalog.service import Registry
from amphora_capability_registry.descriptors.identity import ReleaseDocument
from amphora_capability_registry.descriptors.policy import PermissionPolicy
from amphora_capability_registry.descriptors.requirements import ResourceAllowance

pytestmark=pytest.mark.postgres

def test_rejected_receipt_remains_rejected_after_opt_in_and_accepted_replays_after_removal(registry_env):
    env=registry_env
    descriptor=ReleaseDescriptor.model_validate_json(Path(__file__).with_name("descriptor.json").read_bytes())
    lock=ReleaseDocument.from_descriptor(descriptor).to_lock()
    registered=env.execute("register",{"scope":env.scope.model_dump(),"descriptor":descriptor.model_dump(mode="json"),"expected_lock":lock.model_dump(mode="json")})
    assert registered.status=="accepted"
    payload={"release":lock.model_dump(mode="json"),"expected_revision":1}
    denied=env.execute("activate",payload,command_id="before-opt-in")
    assert denied.reason_code=="activation_profile_denied"
    pins=json.loads(files("amphora_capability_registry.structural_profiles").joinpath("reviewed.json").read_bytes())
    policy=StructuralPolicy((StructuralGrant(env.scope,lock,SchemaRef.model_validate(pins["semantic_profile"])),))
    registry=Registry(env.engine,ResourceAllowance("x86_64","linux",2000,1024,0,300,8,128),PermissionPolicy(),policy)
    def invoke(action,payload,key,principal=env.admin):
        command=parse_registry_command("registry."+action,env.raw(action,payload,principal.actor_id,key))
        return registry.execute(principal,command)
    assert invoke("activate",payload,"before-opt-in")==denied
    accepted=invoke("activate",payload,"after-opt-in")
    assert accepted.status=="accepted"
    assert env.execute("activate",payload,command_id="after-opt-in")==accepted
    assert invoke("deploy",{"deployment_id":"chemical","release":lock.model_dump(mode="json"),"architecture":"x86_64","operating_system":"linux","workers":["worker"]},"deploy").status=="accepted"
    assert invoke("heartbeat",{"deployment_id":"chemical","replica_id":"r","expected_revision":0,"free_slots":1,"ttl_seconds":60},"beat",env.worker).status=="accepted"
    need={"release":lock.model_dump(mode="json"),"context":"supplied-finite-molecules","inputs":[p.model_dump(mode="json") for p in descriptor.tool.inputs],"outputs":[p.model_dump(mode="json") for p in descriptor.tool.outputs]}
    selected=invoke("resolve",need,"select")
    assert selected.status=="accepted" and selected.decision.status=="candidate"
    assert env.execute("resolve",need,command_id="select")==selected
    assert env.execute("resolve",need,command_id="new-unconfigured").status=="rejected"
