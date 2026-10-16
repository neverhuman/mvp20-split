"""Both new operations use the qualified one-attempt public SDK lifecycle."""
from amphora_process_mapping.worker import ProcessWorker

from ..mapping.test_worker import Runtime
from .test_transform import transform_case
from .test_accepted_transform import accepted_case


def test_transform_worker_publishes_proposal_and_completes_only_its_attempt(material_factory):
    _,_,session,client=transform_case(material_factory)
    runtime=Runtime(client,session.attempt.invocation)
    worker=ProcessWorker(runtime,client,"f"*64,operation="transform-materials")
    assert worker.run_once("process-run")["outcome"]=="succeeded"
    assert len(runtime.completed)==1 and len(client.uploads)==3


def test_derivation_worker_reads_existing_proof_and_completes_current_attempt(material_factory):
    c=accepted_case(material_factory)
    runtime=Runtime(c.client,c.session.attempt.invocation)
    runtime.revision=20;c.detail["cut"]["revision"]=20
    runtime.transport=c.runtime.transport
    worker=ProcessWorker(runtime,c.client,"f"*64,operation="derive-process")
    assert worker.run_once("process-run")["outcome"]=="succeeded"
    assert len(runtime.completed)==1 and runtime.completed[0].attempt_id=="derive-attempt"
    assert len(runtime.transport.calls)==3


def test_invalid_source_proof_is_terminal_and_does_not_publish_derivation(material_factory):
    c=accepted_case(material_factory);before=len(c.client.uploads)
    c.detail["attempts"][0]["canonical_result"]=False
    runtime=Runtime(c.client,c.session.attempt.invocation)
    runtime.revision=20;c.detail["cut"]["revision"]=20
    runtime.transport=c.runtime.transport
    worker=ProcessWorker(runtime,c.client,"f"*64,operation="derive-process")
    assert worker.run_once("process-run")["outcome"]=="failed"
    assert runtime.completed[0].outcome.reason_code=="transform_source_not_accepted"
    assert not runtime.completed[0].outcome.retryable and len(c.client.uploads)==before
