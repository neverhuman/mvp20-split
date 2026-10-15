"""Public lifecycle doubles; actual HTTP qualification is a separate gate."""
import hashlib
from datetime import UTC,datetime,timedelta
from types import SimpleNamespace

import pytest
from amphora_tool_protocol import ProtocolError,TransportLost
from amphora_process_mapping.capability import MappingCapability,SCHEMAS
from amphora_process_mapping.payloads import schema_ref
from amphora_process_mapping.worker import MappingWorker

from .test_publication import case


class Runtime:
    def __init__(self,client,invocation):
        self.identity=client.identity
        self.identity.actor_id="mapping-worker"
        self.invocation=invocation;self.completed=[]
        self.until=(datetime.now(UTC)+timedelta(seconds=300)).isoformat()
        self.no_work=False;self.uncertain=False
    def claim(self,run,binding,key,lease_seconds):
        assert binding==self.invocation.tool
        return SimpleNamespace(outcome=SimpleNamespace(status="no_eligible_work" if self.no_work else "claimed",
            invocation=self.invocation,lease_expires_at=self.until))
    def renew(self,attempt,key,lease_seconds,guard):
        guard()
        return SimpleNamespace(outcome=SimpleNamespace(committed=SimpleNamespace(revision=5)))
    def run(self,run):
        attempt=SimpleNamespace(attempt_id=self.invocation.attempt_id,fence=1,worker_id=self.identity.actor_id,
            status="leased",lease_expires_at=self.until,deadline=self.until)
        return SimpleNamespace(status="running",revision=5,activations=[SimpleNamespace(
            invocation_id="invoke",status="leased",fence=1,latest_attempt=attempt)])
    def complete(self,request,key,guard):
        guard();self.completed.append(request.completion)
        if self.uncertain:raise ProtocolError("completion_unknown")
        return SimpleNamespace(outcome=SimpleNamespace(binding=SimpleNamespace(operation_id="completion")))


def worker_case(factory):
    request,session,client=case(factory)
    runtime=Runtime(client,session.attempt.invocation)
    return MappingWorker(runtime,client,"f"*64),runtime,session,client


@pytest.mark.parametrize("record",tuple(SCHEMAS))
def test_schema_bytes_and_descriptor_pins_match(record):
    capability=MappingCapability()
    assert hashlib.sha256(capability.schema_bytes(record)).hexdigest()==schema_ref(*SCHEMAS[record]).sha256
    descriptor=capability.descriptor("f"*64)
    assert descriptor.authority_ceiling=="synthetic_only" and descriptor.egress.mode=="deny"
    assert descriptor.tool.inputs[0].schema_ref==schema_ref(*SCHEMAS["request"])
    assert descriptor.tool.outputs[0].schema_ref==schema_ref(*SCHEMAS["manifest"])


def test_claim_publish_and_same_attempt_completion(material_factory):
    worker,runtime,session,client=worker_case(material_factory)
    result=worker.run_once("process-run")
    assert result==dict(status="completion_accepted",outcome="succeeded",operation_id="completion")
    assert len(runtime.completed)==1 and len(client.uploads)==2
    completion=runtime.completed[0]
    assert completion.attempt_id==session.attempt.invocation.attempt_id and completion.fence==1


def test_no_eligible_work_does_not_read_or_publish(material_factory):
    worker,runtime,_,client=worker_case(material_factory)
    runtime.no_work=True
    assert worker.run_once("process-run")==dict(status="no_eligible_work")
    assert client.uploads=={} and runtime.completed==[]


def test_invalid_input_port_is_terminal_without_publication(material_factory):
    worker,runtime,session,client=worker_case(material_factory)
    session.attempt.invocation.inputs[0].port="wrong"
    assert worker.run_once("process-run")["outcome"]=="failed"
    assert not runtime.completed[0].outcome.retryable and client.uploads=={}


@pytest.mark.parametrize("change",["schema","media","scope"])
def test_input_metadata_rejects_before_reading_bytes(material_factory,change):
    worker,runtime,session,client=worker_case(material_factory)
    ref=session.attempt.invocation.inputs[0].artifact
    if change=="schema":ref=ref.model_copy(update={"schema_ref":ref.schema_ref.model_copy(update={"sha256":"e"*64})})
    if change=="media":ref=ref.model_copy(update={"media_type":"application/octet-stream"})
    if change=="scope":ref=ref.model_copy(update={"scope":ref.scope.model_copy(update={"project_id":"another"})})
    session.attempt.invocation.inputs[0].artifact=ref
    def forbidden(ref):raise AssertionError("metadata must reject before reads")
    client.read=forbidden
    assert worker.run_once("process-run")["outcome"]=="failed"
    assert client.uploads=={} and len(runtime.completed)==1


def test_ambiguous_completion_never_reports_a_contradictory_failure(material_factory):
    worker,runtime,_,_=worker_case(material_factory)
    runtime.uncertain=True
    with pytest.raises(ProtocolError,match="completion_unknown"):worker.run_once("process-run")
    assert len(runtime.completed)==1 and runtime.completed[0].outcome.status=="succeeded"


def test_lost_authority_is_not_reported_as_bad_input(material_factory):
    worker,runtime,session,client=worker_case(material_factory)
    def lost():raise ProtocolError("attempt_authority_lost")
    session.attempt.refresh=lost
    with pytest.raises(ProtocolError,match="authority_lost"):worker.execute(session.attempt)
    assert runtime.completed==[] and client.uploads=={}


def test_transport_failure_is_retryable_only_with_live_attempt(material_factory):
    worker,runtime,_,client=worker_case(material_factory)
    def lost(ref):raise TransportLost("unavailable")
    client.read=lost
    assert worker.run_once("process-run")["outcome"]=="failed"
    assert runtime.completed[0].outcome.retryable and client.uploads=={}
