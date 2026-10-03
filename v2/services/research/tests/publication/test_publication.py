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
from amphora_research.publication.artifact import AssessmentArtifact, SyntheticReceiptPolicy
from amphora_research.publication.store import PublicationStore
from amphora_research.publication.workflow import PublicationWorkflow
from amphora_tool_protocol import CommandRejected, ProtocolError, Reply
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


@pytest.fixture
def publication(assessment_store):
    owner, bound, resolved = assessment_store
    owner.begin(bound)
    owner.complete(bound, resolved)
    store = PublicationStore(owner.engine)
    initial = store.begin(bound.request.profile.scope, bound.request.assessment_id, bound.actor_id, "publisher", "issuer")
    return store, initial


def uploaded(progress):
    return DerivedUploadReceipt(upload=UploadReceipt(upload_id="upload-" + str(progress.ordinal), scope=progress.scope,
        content=progress.artifact.content), declaration=progress.artifact.declaration)


def terminal(progress):
    ref = ArtifactRef(artifact_id="result", scope=progress.scope, **progress.artifact.content.model_dump())
    final = FinalizedReceipt(upload_id=progress.upload.upload.upload_id, artifact=ref)
    command = progress.command("artifacts.begin_derived_upload")
    derivation = DerivationReceipt(origin=command.identity, request_sha256=command.sha256,
        upload_id=final.upload_id, artifact=ref, declaration=progress.artifact.declaration)
    receipt = SyntheticReceiptPolicy().issue(progress.artifact, progress.publisher, progress.issuer, derivation)
    return {"finalized": final.model_dump(mode="json"), "derivation": derivation.model_dump(mode="json"),
            "receipt": receipt.model_dump(mode="json")}


def stream_to_finalize(store, lease):
    p = store.read(lease.initial)
    p = store.advance(lease, p.position, "begun", uploaded(p).model_dump(mode="json"))
    p = store.advance(lease, p.position, "streaming")
    p = store.advance(lease, p.position, "streamed", UploadContentReceipt(upload_id=p.upload.upload.upload_id, attempt_id="stream", generation=1).model_dump(mode="json"))
    return store.advance(lease, p.position, "finalizing")


def test_header_actor_binding_lease_fencing_and_atomic_terminal_replay(publication):
    store, initial = publication
    bound = initial.artifact.stored.intent.bound
    with pytest.raises(AssessmentError, match="actor_mismatch"):
        store.begin(initial.scope, bound.request.assessment_id, "other", "publisher", "issuer")
    with pytest.raises(AssessmentError, match="identity_conflict"):
        store.begin(initial.scope, bound.request.assessment_id, bound.actor_id, "changed", "issuer")
    lease = store.acquire(initial)
    assert store.acquire(initial) is None
    store.renew(lease)
    p = stream_to_finalize(store, lease)
    result = store.advance(lease, p.position, "published", terminal(p))
    assert result.receipt.purpose == "research.synthetic_sufficiency"
    assert result.receipt.outcome.status == "abstained"
    assert PublicationStore(store.engine).read(initial) == result
    with pytest.raises(AssessmentError, match="position_conflict"):
        store.advance(lease, 0, "streaming")
    with pytest.raises(AssessmentError, match="transition_invalid"):
        store.advance(lease, result.position, "streaming")
    store.release(lease)
    newer = store.acquire(initial)
    assert newer.fence == lease.fence + 1
    with pytest.raises(AssessmentError, match="lease_lost"):
        store.renew(lease)
    store.release(newer)


def test_uncertain_streams_are_bounded_and_finalize_identity_is_never_replaced(publication):
    store, initial = publication
    lease = store.acquire(initial)
    progress = initial
    identities = set()
    for ordinal in range(1, 9):
        assert progress.ordinal == ordinal
        identities.add(progress.command_id("artifacts.begin_derived_upload"))
        progress = store.advance(lease, progress.position, "begun", uploaded(progress).model_dump(mode="json"))
        progress = store.advance(lease, progress.position, "streaming")
        progress = store.advance(lease, progress.position, "replace_uncertain_stream")
    assert len(identities) == 8 and progress.stage == "failed"
    assert store.read(initial) == progress
    store.release(lease)
    with pytest.raises(AssessmentError, match="transition_invalid"):
        replace(initial, stage="finalizing").advance("replace_uncertain_stream")


def test_terminal_insert_rollback_cannot_expose_half_receipt(publication):
    store, initial = publication
    lease = store.acquire(initial)
    progress = stream_to_finalize(store, lease)

    def fail(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO research.publication_events"):
            raise RuntimeError("after terminal insert")

    event.listen(store.engine, "after_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError):
            store.advance(lease, progress.position, "published", terminal(progress))
    finally:
        event.remove(store.engine, "after_cursor_execute", fail)
    assert store.read(initial) == progress
    assert store.advance(lease, progress.position, "published", terminal(progress)).stage == "published"
    store.release(lease)


def test_history_cannot_be_mutated_with_service_role(publication):
    store, _ = publication
    for table in ("publication_headers", "publication_events"):
        for action in ("DELETE FROM", "UPDATE"):
            sql = f"{action} research.{table}" + (" SET canonical_bytes=canonical_bytes" if action == "UPDATE" else "")
            with pytest.raises(DBAPIError) as failure, store.engine.begin() as connection:
                connection.execute(text(sql))
            assert failure.value.orig.sqlstate == "42501"


@pytest.mark.parametrize("seconds", [0, 301, True, 1.5])
def test_lease_duration_is_bounded(publication, seconds):
    store, initial = publication
    with pytest.raises(AssessmentError, match="lease_duration"):
        store.acquire(initial, seconds=seconds)


@pytest.mark.parametrize("field", ["sha256", "origin", "receipt"])
def test_terminal_binding_substitution_is_rejected(publication, field):
    store, initial = publication
    lease = store.acquire(initial)
    progress = stream_to_finalize(store, lease)
    data = terminal(progress)
    if field == "sha256":
        data["derivation"]["request_sha256"] = "0" * 64
    elif field == "origin":
        data["derivation"]["origin"]["actor_id"] = "other"
    else:
        data["receipt"]["purpose"] = "scientific"
    with pytest.raises(AssessmentError, match="mismatch"):
        store.advance(lease, progress.position, "published", data)
    assert store.read(initial).stage == "finalizing"
    store.release(lease)


@pytest.mark.parametrize("stage", ["begin", "stream", "finalize", None])
def test_workflow_recovers_lost_ack_without_replacing_finalize(publication, monkeypatch, stage):
    store, initial = publication
    bound = initial.artifact.stored.intent.bound
    failures, begin_ids, final_ids = [], [], []
    current = {"progress": initial}

    class Reader:
        scope = initial.scope

        def read(self, reference):
            assert store.engine.pool.checkedout() == 0

    class Client:
        def __init__(self, *args):
            pass

        def maybe_fail(self, name):
            if stage == name and not failures:
                failures.append(name)
                raise ProtocolError("lost_ack")

        def begin_derived(self, content, declaration, identity, **kw):
            kw["guard"]()
            begin_ids.append(identity)
            self.maybe_fail("begin")
            current["progress"] = store.read(initial)
            return uploaded(current["progress"])

        def stream(self, upload, body, **kw):
            kw["guard"]()
            self.maybe_fail("stream")
            return UploadContentReceipt(upload_id=upload.upload_id, attempt_id="stream", generation=1)

        def finalize(self, upload, identity, **kw):
            kw["guard"]()
            final_ids.append(identity)
            current["progress"] = store.read(initial)
            self.maybe_fail("finalize")
            return FinalizedReceipt.model_validate_json(json.dumps(terminal(current["progress"])["finalized"]))

        def derivation(self, reference):
            return DerivationReceipt.model_validate_json(json.dumps(terminal(current["progress"])["derivation"]))

    monkeypatch.setattr("amphora_research.publication.workflow.ArtifactClient", Client)
    workflow = PublicationWorkflow(store, Reader(), None, "publisher", "issuer")
    if stage is not None:
        with pytest.raises(ProtocolError, match="lost_ack"):
            workflow.submit(initial.scope, bound.request.assessment_id, bound.actor_id)
    result = workflow.submit(initial.scope, bound.request.assessment_id, bound.actor_id)
    assert result.stage == "published"
    assert result.ordinal == (2 if stage == "stream" else 1)
    assert len(set(final_ids)) == 1
    if stage == "begin":
        assert len(set(begin_ids)) == 1
    assert workflow.submit(initial.scope, bound.request.assessment_id, bound.actor_id) == result


def test_artifact_rejects_pending_and_receipt_cannot_promote_inconsistent_assessment(publication):
    _, initial = publication
    with pytest.raises(AssessmentError, match="assessment_pending"):
        AssessmentArtifact.from_stored(replace(initial.artifact.stored, resolved=None))
    result = initial.artifact.stored.resolved.assessment
    with pytest.raises(AssessmentError, match="inconsistent"):
        SyntheticReceiptPolicy.disposition(result.model_copy(update={"sufficient": True}))
    assert SyntheticReceiptPolicy.disposition(result.model_copy(update={"disposition": "contradicted"}))[0] == "rejected"


def test_expired_holder_cannot_write_after_replacement(publication):
    store, initial = publication
    old = store.acquire(initial, seconds=1)
    time.sleep(1.1)
    newer = store.acquire(initial)
    assert newer.fence == old.fence + 1
    with pytest.raises(AssessmentError, match="lease_lost"):
        store.advance(old, 0, "denied", "denied")
    assert store.read(initial).position == 0
    store.release(newer)


@pytest.mark.parametrize("unavailable", [False, True])
def test_denied_input_is_terminal_but_unavailable_input_stays_pending(publication, unavailable):
    store, initial = publication
    bound = initial.artifact.stored.intent.bound

    class Reader:
        scope = initial.scope

        def read(self, reference):
            raise (AssessmentPeerUnavailable("offline") if unavailable else AssessmentError("peer_access_denied"))

    workflow = PublicationWorkflow(store, Reader(), None, "publisher", "issuer")
    if unavailable:
        with pytest.raises(AssessmentPeerUnavailable):
            workflow.submit(initial.scope, bound.request.assessment_id, bound.actor_id)
        assert store.read(initial).stage == "prepared"
    else:
        result = workflow.submit(initial.scope, bound.request.assessment_id, bound.actor_id)
        assert result.stage == "failed" and result.failure == "peer_access_denied" and result.receipt is None
        assert workflow.submit(initial.scope, bound.request.assessment_id, bound.actor_id) == result


@pytest.mark.parametrize("finalizing", [False, True])
@pytest.mark.parametrize("mismatch", [False, True])
def test_only_exact_original_command_rejection_can_fail_publication(publication, finalizing, mismatch):
    store, initial = publication
    lease = store.acquire(initial)
    progress = stream_to_finalize(store, lease) if finalizing else initial
    family = "artifacts.finalize" if finalizing else "artifacts.begin_derived_upload"
    command = progress.command(family)
    proof = {"schema_version": "1", "identity": command.identity.model_dump(mode="json"),
             "request_sha256": "0" * 64 if mismatch else command.sha256, "operation_id": "original",
             "outcome": {"status": "rejected", "reason_code": "source_revoked"}}
    if mismatch:
        with pytest.raises(AssessmentError, match="rejection_mismatch"):
            store.advance(lease, progress.position, "rejected", proof)
        assert store.read(initial) == progress
    else:
        result = store.advance(lease, progress.position, "rejected", proof)
        assert result.stage == "failed" and result.failure == "source_revoked" and result.receipt is None
    store.release(lease)


@pytest.mark.parametrize("kind", ["upload", "stream", "derivation"])
def test_stage_payload_substitution_is_rejected(publication, kind):
    _, initial = publication
    if kind == "upload":
        data = uploaded(initial).model_dump(mode="json")
        data["upload"]["content"]["sha256"] = "0" * 64
        with pytest.raises(AssessmentError, match="upload_mismatch"):
            initial.advance("begun", data)
    elif kind == "stream":
        p = initial.advance("begun", uploaded(initial).model_dump(mode="json")).advance("streaming")
        with pytest.raises(AssessmentError, match="stream_mismatch"):
            p.advance("streamed", UploadContentReceipt(upload_id="other", attempt_id="stream", generation=1).model_dump(mode="json"))
    else:
        p = replace(initial, stage="finalizing", upload=uploaded(initial))
        data = terminal(p)
        derivation = DerivationReceipt.model_validate_json(json.dumps(data["derivation"]))
        derivation = derivation.model_copy(update={"artifact": derivation.artifact.model_copy(update={"sha256": "0" * 64})})
        with pytest.raises(AssessmentError, match="derivation_mismatch"):
            SyntheticReceiptPolicy().issue(p.artifact, p.publisher, p.issuer, derivation)


def test_payload_schema_and_method_bind_exact_stored_profile(publication):
    import hashlib

    from jsonschema import Draft202012Validator

    _, initial = publication
    schema = AssessmentArtifact.schema_document()
    Draft202012Validator(json.loads(schema)).validate(json.loads(initial.artifact.body))
    assert initial.artifact.content.schema_ref.sha256 == hashlib.sha256(schema).hexdigest()
    assert initial.artifact.stored.resolved.assessment.scientifically_established is False
    assert initial.command_id("artifacts.finalize") != initial.command_id("artifacts.begin_derived_upload")


@pytest.mark.parametrize("finalizing", [False, True])
@pytest.mark.parametrize("proof_available", [False, True])
def test_workflow_requires_retained_rejection_proof_before_terminal_failure(publication, monkeypatch, finalizing, proof_available):
    store, initial = publication
    if finalizing:
        lease = store.acquire(initial)
        stream_to_finalize(store, lease)
        store.release(lease)
    progress = store.read(initial)
    family = "artifacts.finalize" if finalizing else "artifacts.begin_derived_upload"
    command = progress.command(family)
    proof = {"schema_version": "1", "identity": command.identity.model_dump(mode="json"),
             "request_sha256": command.sha256, "operation_id": "original",
             "outcome": {"status": "rejected", "reason_code": "source_revoked"}}

    class Reader:
        scope = initial.scope

        def read(self, reference):
            pass

    class Client:
        def __init__(self, *args):
            pass

        def begin_derived(self, *args, **kwargs):
            raise CommandRejected("source_revoked")

        def finalize(self, *args, **kwargs):
            raise CommandRejected("source_revoked")

    class Transport:
        def request(self, method, path):
            assert path.endswith(command.identity.command_id)
            return Reply(200 if proof_available else 503, json.dumps(proof).encode())

    monkeypatch.setattr("amphora_research.publication.workflow.ArtifactClient", Client)
    workflow = PublicationWorkflow(store, Reader(), Transport(), "publisher", "issuer")
    bound = initial.artifact.stored.intent.bound
    if proof_available:
        result = workflow.submit(initial.scope, bound.request.assessment_id, bound.actor_id)
        assert result.stage == "failed" and result.failure == "source_revoked"
        assert result.receipt is None
    else:
        with pytest.raises(ProtocolError, match="rejection_unavailable"):
            workflow.submit(initial.scope, bound.request.assessment_id, bound.actor_id)
        assert store.read(initial) == progress
