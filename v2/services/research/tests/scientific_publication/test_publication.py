"""Scientific Artifact publication preserves uncertain effects without granting Runtime authority."""
import json
import time
from dataclasses import replace

import pytest
from amphora_contracts_artifacts import (
    DerivationReceipt,
    DerivedUploadReceipt,
    FinalizedReceipt,
    UploadContentReceipt,
    UploadReceipt,
)
from amphora_contracts_core import ArtifactRef
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentPeerUnavailable
from amphora_research.scientific_publication.artifact import ScientificArtifact, ScientificPublicationError
from amphora_research.scientific_publication.store import ScientificPublicationStore
from amphora_research.scientific_publication.workflow import ScientificPublicationWorkflow
from amphora_tool_protocol import CommandRejected, ProtocolError, Reply
from sqlalchemy import event, text

from ..eligibility.test_store import prepared_case
from ..observations.test_intake_store import stored_case
from ..synthesis.test_store import prepared_case as synthesis_case

pytestmark = pytest.mark.postgres


def publication(ledger, kind="eligibility"):
    if kind == "lab-intake":
        store,intent,resolved = stored_case(ledger)
        store.begin(intent)
        artifact = ScientificArtifact.from_intake(store.complete(intent,resolved))
        engine = store.engine
    else:
        values = prepared_case(ledger) if kind == "eligibility" else synthesis_case(ledger)
        store,policy,inputs = values[:3]
        artifact = ScientificArtifact.from_decision(store.assess(policy,inputs,"fixture","decision"))
        engine = store.journal.engine
    journal = ScientificPublicationStore(engine)
    return journal,journal.begin(artifact,"publisher")


def uploaded(progress):
    return DerivedUploadReceipt(upload=UploadReceipt(upload_id="upload-"+str(progress.ordinal),scope=progress.scope,
        content=progress.artifact.content),declaration=progress.artifact.declaration)


def terminal(progress):
    reference = ArtifactRef(artifact_id="scientific-result",scope=progress.scope,**progress.artifact.content.model_dump())
    final = FinalizedReceipt(upload_id=progress.upload.upload.upload_id,artifact=reference)
    command = progress.command("artifacts.begin_derived_upload")
    derivation = DerivationReceipt(origin=command.identity,request_sha256=command.sha256,upload_id=final.upload_id,
                                  artifact=reference,declaration=progress.artifact.declaration)
    return {"finalized":final.model_dump(mode="json"),"derivation":derivation.model_dump(mode="json")}


def finalizing(store, lease):
    progress = store.read(lease.initial)
    progress = store.advance(lease,progress.position,"begun",uploaded(progress).model_dump(mode="json"))
    progress = store.advance(lease,progress.position,"streaming")
    receipt = UploadContentReceipt(upload_id=progress.upload.upload.upload_id,attempt_id="stream",generation=1)
    progress = store.advance(lease,progress.position,"streamed",receipt.model_dump(mode="json"))
    return store.advance(lease,progress.position,"finalizing")


@pytest.mark.parametrize("kind",["lab-intake","eligibility","synthesis"])
def test_exact_publication_history_rebuilds_without_runtime_receipt(ledger,kind):
    store,initial = publication(ledger,kind)
    lease = store.acquire(initial)
    assert store.acquire(initial) is None
    store.renew(lease)
    progress = finalizing(store,lease)
    result = store.advance(lease,progress.position,"published",terminal(progress))
    assert result.stage == "published" and result.derivation is not None
    assert not hasattr(result,"receipt")
    assert ScientificPublicationStore(store.engine).read(initial) == result
    assert store.begin(initial.artifact,"publisher") == initial
    with pytest.raises(ScientificPublicationError,match="identity_conflict"):
        store.begin(initial.artifact,"different-publisher")
    store.release(lease)


@pytest.mark.parametrize("field",["body","declaration"])
def test_submitted_payload_must_match_committed_owner_record(ledger,field):
    store,initial = publication(ledger)
    altered = replace(initial.artifact,**{field:b"forged" if field == "body" else
        initial.artifact.declaration.model_copy(update={"inputs":initial.artifact.declaration.inputs[:1]})})
    with pytest.raises(ScientificPublicationError,match="source_mismatch"):
        store.begin(altered,"publisher")


@pytest.mark.parametrize("field",["receipt","origin","sha256","content","declaration"])
def test_terminal_proof_cannot_be_substituted_or_promote_receipt_authority(ledger,field):
    store,initial = publication(ledger)
    lease = store.acquire(initial)
    progress = finalizing(store,lease)
    proof = terminal(progress)
    if field == "receipt":
        proof["receipt"] = {"purpose":"research.synthetic_sufficiency"}
    elif field == "origin":
        proof["derivation"]["origin"]["actor_id"] = "other"
    elif field == "sha256":
        proof["derivation"]["request_sha256"] = "0"*64
    elif field == "content":
        proof["derivation"]["artifact"]["sha256"] = "0"*64
        proof["finalized"]["artifact"]["sha256"] = "0"*64
    else:
        proof["derivation"]["declaration"]["transformation"]["version"] = "2"
    with pytest.raises(ScientificPublicationError,match="shape|mismatch"):
        store.advance(lease,progress.position,"published",proof)
    assert store.read(initial).stage == "finalizing"
    store.release(lease)


@pytest.mark.parametrize("lost",[None,"begin","stream","finalize","derivation"])
def test_workflow_replays_uncertain_commands_and_replaces_only_uncertain_streams(ledger,monkeypatch,lost):
    store,initial = publication(ledger)
    failed,begin_ids,final_ids = [],[],[]
    class Reader:
        scope = initial.scope
        def read(self, reference):
            assert store.engine.pool.checkedout() == 0
    class Client:
        def __init__(self,*args):
            pass
        def fault(self, where):
            if lost == where and not failed:
                failed.append(where)
                raise ProtocolError("lost_ack")
        def begin_derived(self,content,declaration,identity,**kwargs):
            kwargs["guard"]()
            begin_ids.append(identity)
            self.fault("begin")
            return uploaded(store.read(initial))
        def stream(self,upload,body,**kwargs):
            kwargs["guard"]()
            self.fault("stream")
            return UploadContentReceipt(upload_id=upload.upload_id,attempt_id="stream",generation=1)
        def finalize(self,upload,identity,**kwargs):
            kwargs["guard"]()
            final_ids.append(identity)
            self.fault("finalize")
            return FinalizedReceipt.model_validate_json(json.dumps(terminal(store.read(initial))["finalized"]))
        def derivation(self,reference):
            self.fault("derivation")
            return DerivationReceipt.model_validate_json(json.dumps(terminal(store.read(initial))["derivation"]))
    monkeypatch.setattr("amphora_research.scientific_publication.workflow.ArtifactClient",Client)
    workflow = ScientificPublicationWorkflow(store,Reader(),None,"publisher")
    if lost is not None:
        with pytest.raises(ProtocolError,match="lost_ack"):
            workflow.submit(initial.artifact)
    result = workflow.submit(initial.artifact)
    assert result.stage == "published" and result.ordinal == (2 if lost == "stream" else 1)
    assert len(set(final_ids)) == 1
    if lost == "begin":
        assert len(set(begin_ids)) == 1
    assert workflow.submit(initial.artifact) == result


@pytest.mark.parametrize("unavailable",[False,True])
def test_source_denial_and_outage_have_distinct_outcomes(ledger,unavailable):
    store,initial = publication(ledger)
    class Reader:
        scope = initial.scope
        def read(self, reference):
            raise AssessmentPeerUnavailable("offline") if unavailable else AssessmentError("peer_access_denied")
    workflow = ScientificPublicationWorkflow(store,Reader(),None,"publisher")
    if unavailable:
        with pytest.raises(AssessmentPeerUnavailable):
            workflow.submit(initial.artifact)
        assert store.read(initial).stage == "prepared"
    else:
        result = workflow.submit(initial.artifact)
        assert result.stage == "failed" and result.failure == "peer_access_denied"
        assert workflow.submit(initial.artifact) == result


def test_old_fence_cannot_append_after_lease_replacement(ledger):
    store,initial = publication(ledger)
    old = store.acquire(initial,seconds=1)
    time.sleep(1.1)
    current = store.acquire(initial)
    assert current.fence == old.fence+1
    with pytest.raises(ScientificPublicationError,match="lease_lost"):
        store.advance(old,0,"denied","denied")
    assert store.read(initial).position == 0
    store.release(current)


def test_scientific_publication_grants_keep_headers_and_events_append_only(ledger):
    store,_ = publication(ledger)
    with store.engine.connect() as connection:
        for table in ("science_publication_headers","science_publication_events"):
            for privilege in ("UPDATE","DELETE","TRUNCATE"):
                assert not connection.execute(text("SELECT has_table_privilege(current_user,:table,:privilege)"),
                    {"table":"research."+table,"privilege":privilege}).scalar_one()


@pytest.mark.parametrize("final_stage",[False,True])
@pytest.mark.parametrize("available",[False,True])
def test_workflow_requires_exact_retained_rejection_proof(ledger,monkeypatch,final_stage,available):
    store,initial = publication(ledger)
    if final_stage:
        lease = store.acquire(initial)
        finalizing(store,lease)
        store.release(lease)
    progress = store.read(initial)
    family = "artifacts.finalize" if final_stage else "artifacts.begin_derived_upload"
    command = progress.command(family)
    proof = {"schema_version":"1","identity":command.identity.model_dump(mode="json"),"request_sha256":command.sha256,
        "operation_id":"original","outcome":{"status":"rejected","reason_code":"source_revoked"}}
    class Reader:
        scope = initial.scope
        def read(self,reference):
            pass
    class Client:
        def __init__(self,*args):
            pass
        def begin_derived(self,*args,**kwargs):
            raise CommandRejected("source_revoked")
        def finalize(self,*args,**kwargs):
            raise CommandRejected("source_revoked")
    class Transport:
        def request(self,method,path):
            assert path.endswith(command.identity.command_id)
            return Reply(200 if available else 503,json.dumps(proof).encode())
    monkeypatch.setattr("amphora_research.scientific_publication.workflow.ArtifactClient",Client)
    workflow = ScientificPublicationWorkflow(store,Reader(),Transport(),"publisher")
    if available:
        result = workflow.submit(initial.artifact)
        assert result.stage == "failed" and result.failure == "source_revoked" and result.derivation is None
    else:
        with pytest.raises(ProtocolError,match="rejection_unavailable"):
            workflow.submit(initial.artifact)
        assert store.read(initial) == progress


def test_eight_uncertain_streams_exhaust_budget_without_fabricating_publication(ledger):
    store,initial = publication(ledger)
    lease = store.acquire(initial)
    progress = initial
    for ordinal in range(1,9):
        assert progress.ordinal == ordinal
        progress = store.advance(lease,progress.position,"begun",uploaded(progress).model_dump(mode="json"))
        progress = store.advance(lease,progress.position,"streaming")
        progress = store.advance(lease,progress.position,"replace_uncertain_stream")
    assert progress.stage == "failed" and progress.failure == "science_publication_attempt_limit"
    assert progress.derivation is None and store.read(initial) == progress
    store.release(lease)


def test_failed_event_insert_rolls_back_progress_and_stale_position_cannot_advance(ledger):
    store,initial = publication(ledger)
    lease = store.acquire(initial)
    def fault(connection,cursor,statement,parameters,context,executemany):
        if statement.startswith("INSERT INTO research.science_publication_events"):
            raise RuntimeError("simulated event failure")
    event.listen(store.engine,"before_cursor_execute",fault)
    try:
        with pytest.raises(RuntimeError,match="simulated event failure"):
            store.advance(lease,0,"begun",uploaded(initial).model_dump(mode="json"))
    finally:
        event.remove(store.engine,"before_cursor_execute",fault)
    assert store.read(initial) == initial
    changed = store.advance(lease,0,"begun",uploaded(initial).model_dump(mode="json"))
    with pytest.raises(ScientificPublicationError,match="position_conflict"):
        store.advance(lease,0,"streaming")
    assert store.read(initial) == changed
    store.release(lease)


@pytest.mark.parametrize("kind",["upload","stream","rejection"])
def test_stage_mismatches_leave_last_verified_position_intact(ledger,kind):
    _,initial = publication(ledger)
    if kind == "upload":
        value = uploaded(initial).model_dump(mode="json")
        value["upload"]["content"]["sha256"] = "0"*64
        with pytest.raises(ScientificPublicationError,match="upload_mismatch"):
            initial.advance("begun",value)
    elif kind == "stream":
        progress = initial.advance("begun",uploaded(initial).model_dump(mode="json")).advance("streaming")
        with pytest.raises(ScientificPublicationError,match="stream_mismatch"):
            progress.advance("streamed",UploadContentReceipt(upload_id="other",attempt_id="stream",generation=1).model_dump(mode="json"))
    else:
        command = initial.command("artifacts.begin_derived_upload")
        proof = {"schema_version":"1","identity":command.identity.model_dump(mode="json"),"request_sha256":"0"*64,
            "operation_id":"original","outcome":{"status":"rejected","reason_code":"source_revoked"}}
        with pytest.raises(ScientificPublicationError,match="rejection_mismatch"):
            initial.advance("rejected",proof)


def test_busy_workflow_defers_to_current_lease_and_illegal_transition_is_rejected(ledger):
    store,initial = publication(ledger)
    lease = store.acquire(initial)
    assert ScientificPublicationWorkflow(store,None,None,"publisher").submit(initial.artifact) == initial
    with pytest.raises(ScientificPublicationError,match="transition_invalid"):
        store.advance(lease,0,"finalizing")
    for seconds in (0,301,True):
        with pytest.raises(ScientificPublicationError,match="lease_duration"):
            store.renew(lease,seconds)
    store.release(lease)
