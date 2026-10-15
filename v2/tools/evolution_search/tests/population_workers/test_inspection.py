"""Public owner-record identity/cut checks; scripted transport, no acceptance claim."""
import copy
import json
from types import SimpleNamespace

import pytest
from amphora_contracts_core import Scope
from amphora_evolution_search.population_workers.inspection import ObservationChanged, PopulationInspection
from amphora_tool_protocol import ProtocolError, Reply

from .conftest import Attempt


def records():
    from pathlib import Path
    # Existing reviewed PreparedInvocation fixture, copied into this owner's tests.
    invocation = json.loads(Path(__file__).with_name("inspection-prepared.json").read_bytes())
    scope = invocation["inputs"][0]["artifact"]["scope"]
    activation = "a"*64
    invocation.update(activation_id=activation, invocation_id=activation, node_id="cost")
    node = dict(activation_id=activation,path=dict(schema_version="2",node_id="cost",occurrences=[]),
        kind="invoke",status="succeeded",reason_code=None)
    cut=dict(scope=scope,run_id="run",plan_sha256="f"*64,revision=10,frontier_revision=2)
    snapshot=dict(cut=cut,status="running",budget=dict(limit=20,reserved=1,spent=9),
        query=dict(scope_key=None,frontier_only=False),node_count=1,snapshot_token="snapshot",event_cursor="events")
    attempt=dict(attempt_id="attempt",invocation_id=activation,worker_id="worker",fence=1,status="succeeded",
        settled=True,completion_id="completion",canonical_result=True)
    detail=dict(cut=cut,node=node,scope_key="b"*64,parent_activation_id=None,outputs=[],attempts=[attempt],next_cursor=None)
    inputs=dict(schema_version="1",profile="runtime-node-inputs-v1",scope=scope,run_id="run",activation_id=activation,
        scope_key="b"*64,observed_run_revision=10,scope_inputs=[],invocation=invocation)
    completion=dict(scope=scope,run_id="run",completion_id="completion",activation_id=activation,
        accepted_run_revision=8,canonical_result=True,retention_reservation_ids=["reservation"],
        result=dict(schema_version="1",invocation_id=activation,attempt_id="attempt",fence=1,
            outcome=dict(status="succeeded",outputs=[dict(port="result",artifact=invocation["inputs"][0]["artifact"])])))
    proof=dict(wire_version="1",authority="accepted_execution",worker_id="worker",invocation=invocation,completion=completion)
    return SimpleNamespace(scope=Scope.model_validate(scope),node=node,snapshot=snapshot,detail=detail,inputs=inputs,proof=proof)


class Scripted:
    def __init__(self, replies): self.replies=list(replies);self.calls=[]
    def request(self,method,path,**kwargs):
        self.calls.append((method,path,kwargs))
        result=self.replies.pop(0)
        return result if isinstance(result,Reply) else Reply(200,json.dumps(result).encode())


def reader(e,*responses):
    attempt=Attempt();transport=Scripted(responses)
    runtime=SimpleNamespace(identity=SimpleNamespace(scope=e.scope),transport=transport)
    return PopulationInspection(runtime,attempt),attempt,transport


def page(e): return dict(snapshot=e.snapshot,nodes=[e.node],next_cursor=None)


def test_success_binds_prepared_inputs_canonical_attempt_and_producer():
    e=records();reads,attempt,transport=reader(e,page(e),e.detail,e.inputs,e.proof)
    cut=reads.capture("run",10)
    result=reads.method(cut,cut.nodes[0])
    assert result.producer.invocation==result.inputs.invocation
    assert result.completion.completion_id=="completion"
    assert attempt.refreshes==1 # Renewal between cut-bound pages would invalidate the cut.
    assert all(method=="GET" for method,_,_ in transport.calls)


@pytest.mark.parametrize("change",["missing","duplicate","mixed"])
def test_incomplete_duplicate_or_mixed_snapshot_rejects(change):
    e=records();first=page(e);second=copy.deepcopy(first)
    if change=="missing": first["snapshot"]["node_count"]=2
    if change in {"duplicate","mixed"}:
        first["snapshot"]["node_count"]=2;first["next_cursor"]="next"
        second["snapshot"]["node_count"]=2
        if change=="mixed": second["snapshot"]["cut"]["revision"]=11
    reads,_,_=reader(e,first,second)
    with pytest.raises(ValueError): reads.capture("run",10)


def test_pagination_preserves_frozen_snapshot_and_checks_full_count():
    e=records();first=page(e);first["snapshot"]["node_count"]=2;first["next_cursor"]="next"
    second=copy.deepcopy(first);second["next_cursor"]=None;second["nodes"][0]["activation_id"]="c"*64
    reads,_,transport=reader(e,first,second)
    assert len(reads.capture("run",10).nodes)==2
    assert transport.calls[1][2]["query"]=={"limit":100,"cursor":"next"}


@pytest.mark.parametrize("change",["inputs","attempt","completion","worker","future","scope"])
def test_unrelated_producer_or_input_rejects(change):
    e=records();e.proof=copy.deepcopy(e.proof)
    if change=="inputs": e.proof["invocation"]["inputs"][0]["artifact"]["artifact_id"]="other"
    if change=="attempt": e.proof["completion"]["result"]["attempt_id"]="other"
    if change=="completion": e.proof["completion"]["completion_id"]="other"
    if change=="worker": e.proof["worker_id"]="other"
    if change=="future": e.proof["completion"]["accepted_run_revision"]=11
    if change=="scope": e.proof["completion"]["scope"]["project_id"]="other"
    reads,_,_=reader(e,page(e),e.detail,e.inputs,e.proof);cut=reads.capture("run",10)
    with pytest.raises(ValueError): reads.method(cut,cut.nodes[0])


@pytest.mark.parametrize("status",["skipped","expired"])
def test_missing_output_retains_owner_inputs_without_success_producer_lookup(status):
    e=records();e.node["status"]="skipped" if status=="skipped" else "failed"
    if status=="skipped": e.inputs["invocation"]=None;e.detail["attempts"]=[]
    else:
        e.detail["attempts"][0].update(status="expired",canonical_result=False,completion_id=None)
    reads,_,transport=reader(e,page(e),e.detail,e.inputs);cut=reads.capture("run",10)
    observed=reads.method(cut,cut.nodes[0])
    assert observed.producer is None and observed.completion is None
    assert not any(path.endswith("/producer") for _,path,_ in transport.calls)


@pytest.mark.parametrize("status,error",[(409,ObservationChanged),(403,ProtocolError),(503,ProtocolError)])
def test_owner_failure_does_not_become_empty_observation_set(status,error):
    e=records();reads,_,_=reader(e,Reply(status,b"sensitive diagnostic"))
    with pytest.raises(error,match="^population_observation_"):reads.capture("run",10)


def test_lost_attempt_authority_stops_reads_before_http():
    e=records();reads,attempt,transport=reader(e,page(e));attempt.live=False
    with pytest.raises(ProtocolError,match="attempt_authority_lost"): reads.capture("run",10)
    assert transport.calls==[]
