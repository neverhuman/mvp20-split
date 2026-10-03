"""Actual bounded source-to-vector orchestration and interruption recovery."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_contracts_representations import representation_vector_schema
from amphora_data_artifacts.publication.model import ContentPolicy, UploadError
from amphora_data_artifacts.representations.bindings.content_rule import VectorContentRule
from amphora_data_artifacts.representations.bindings.workflow import BindingWorkflow, RecoveryBudget
from amphora_data_artifacts.representations.validation import RepresentationError
from amphora_data_artifacts.source_rights.model import RightsError
from amphora_data_artifacts.storage.local import ByteWriter
from sqlalchemy import text

pytestmark = pytest.mark.postgres


@pytest.fixture
def flow(source_setup):
    e = source_setup
    principal = replace(e.principal, actions=e.principal.actions | {"upload", "finalize"})
    uploads = e.e.env.uploads
    ref = representation_vector_schema()
    policy = uploads.policy
    uploads.policy = ContentPolicy(
        policy.allowed | {("application/json", ref.schema_id, ref.version, ref.sha256)},
        rules=policy.rules + (VectorContentRule(),),
    )
    workflow = BindingWorkflow(e.e.reads, uploads, e.e.env.storage)
    return SimpleNamespace(
        e=e,
        p=principal,
        workflow=workflow,
        uploads=uploads,
        engine=e.e.env.engine,
        storage=e.e.env.storage,
        request=e.request,
    )


def encode(e):
    return e.workflow.encode(e.p, e.request)


def stopped_at_upload(e):
    e.workflow.budget = RecoveryBudget(2)
    assert encode(e).outcome.state == "pending"
    lease = e.workflow.claims.claim(e.p, e.e.preflight.load(e.p, e.request).identity.binding_id)
    prefix = e.workflow.journal.read(e.p, lease)
    assert prefix.stage == "upload_begun"
    e.workflow.claims.release(e.p, lease)
    e.workflow.budget = RecoveryBudget()
    return prefix


def test_actual_encoding_alias_and_offline_exact_replay(flow, monkeypatch):
    e = flow
    result = encode(e)
    assert result.outcome.state == "published"
    artifact, payload = e.e.e.reads.content(e.p, result.outcome.binding.vector.artifact_id)
    assert artifact.reference == result.outcome.binding.vector and b"payload_hex" in payload
    alias = e.request.model_copy(update={"encoding_id": "second"})
    assert e.workflow.encode(e.p, alias).outcome == result.outcome

    def unavailable(*args):
        raise AssertionError("historical result must not reread source")

    monkeypatch.setattr(e.workflow.preflight, "load", unavailable)
    assert encode(e) == result
    wrong = e.request.model_copy(update={"source": e.request.source.model_copy(update={"start": 8})})
    with pytest.raises(RepresentationError, match="request_conflict"):
        e.workflow.encode(e.p, wrong)


def test_every_grant_precedes_side_effects_and_budget_is_bounded(flow):
    e = flow
    for action in (
        "representation_encode",
        "representation_read",
        "source_history",
        "read",
        "upload",
        "finalize",
    ):
        with pytest.raises(UploadError, match="access_denied"):
            e.workflow.encode(replace(e.p, actions=e.p.actions - {action}), e.request)
    assert e.workflow.requests.read(e.p, e.request.encoding_id) is None
    for value in (0, 65, True):
        with pytest.raises(RepresentationError, match="recovery_bound"):
            RecoveryBudget(value)
    e.workflow.budget = RecoveryBudget(1)
    outcomes = [encode(e).outcome.state for _ in range(7)]
    assert outcomes == ["pending"] * 5 + ["published"] * 2


def test_compute_and_publication_busy_are_retained_pending(flow):
    e = flow
    prepared = e.e.preflight.load(e.p, e.request)
    compute = e.workflow.compute.claim(e.p, e.request.profile, prepared.input)
    assert encode(e).outcome.state == "pending"
    e.workflow.compute.release(e.p, compute)
    e.workflow.budget = RecoveryBudget(1)
    assert encode(e).outcome.state == "pending"
    lease = e.workflow.claims.claim(e.p, prepared.identity.binding_id)
    assert encode(e).outcome.state == "pending"
    e.workflow.claims.release(e.p, lease)
    e.workflow.budget = RecoveryBudget()
    assert encode(e).outcome.state == "published"


@pytest.mark.parametrize(
    "owner,method", [("derived", "begin"), ("finalizer", "finalize"), ("journal", "publish")]
)
def test_lost_effect_response_recovers_same_publication(flow, monkeypatch, owner, method):
    e = flow
    target = getattr(e.workflow, owner)
    original = getattr(target, method)
    effects = []

    def lost(*args, **kwargs):
        result = original(*args, **kwargs)
        effects.append(result)
        raise OSError("lost acknowledgement")

    monkeypatch.setattr(target, method, lost)
    with pytest.raises(OSError, match="lost acknowledgement"):
        encode(e)
    monkeypatch.setattr(target, method, original)
    # Reconstruct the entire workflow, retaining PostgreSQL and local Artifact bytes.
    e.workflow = BindingWorkflow(e.e.e.reads, e.uploads, e.storage)
    recovered = encode(e)
    assert recovered.outcome.state == "published" and len(effects) == 1
    with e.engine.connect() as c:
        assert (
            c.execute(
                text(
                    "SELECT count(*) FROM artifacts.derivations WHERE tenant_id=:tenant AND project_id=:project"
                ),
                e.p.bindings,
            ).scalar_one()
            == 1
        )
    if method == "finalize":
        assert recovered.outcome.binding.vector == effects[0].artifact
    elif method == "publish":
        assert recovered.outcome.binding == effects[0]


def test_writer_failure_closes_and_settles_before_retry(flow, monkeypatch):
    e = flow
    original = ByteWriter.write

    def partial(self, content):
        original(self, content[:2])
        raise OSError("interrupted write")

    monkeypatch.setattr(ByteWriter, "write", partial)
    with pytest.raises(OSError, match="interrupted write"):
        encode(e)
    with e.engine.connect() as c:
        assert (
            c.execute(
                text(
                    "SELECT active_streams FROM artifacts.capacity WHERE tenant_id=:tenant AND project_id=:project"
                ),
                e.p.bindings,
            ).scalar_one()
            == 0
        )
    monkeypatch.setattr(ByteWriter, "write", original)
    assert encode(e).outcome.state == "published"


def test_lost_stream_settlement_reuses_existing_selection(flow, monkeypatch):
    e = flow
    original = e.uploads.finish
    once = []

    def lost(*args, **kwargs):
        result = original(*args, **kwargs)
        if kwargs["verified"] and not once:
            once.append(True)
            raise OSError("settlement acknowledgement lost")
        return result

    monkeypatch.setattr(e.uploads, "finish", lost)
    with pytest.raises(OSError, match="acknowledgement lost"):
        encode(e)
    monkeypatch.setattr(e.uploads, "finish", original)
    assert encode(e).outcome.state == "published"


def test_expired_stream_is_fenced_without_deletion_then_recovered(flow):
    e = flow
    prefix = stopped_at_upload(e)
    e.uploads.limits = replace(e.uploads.limits, seconds=1)
    attempt = e.uploads.start(e.p, prefix.upload_id)
    writer = e.storage.writer(attempt)
    writer.write(b"partial")
    writer.close()
    assert encode(e).outcome.state == "pending"
    with e.engine.connect() as c:
        c.execute(text("SELECT pg_sleep(1.05)"))
    assert encode(e).outcome.state == "published"
    assert e.storage.path(attempt.storage_key).read_bytes() == b"partial"
    with pytest.raises(UploadError, match="storage_key_retired"):
        e.storage.writer(attempt)
    with e.engine.connect() as c:
        assert (
            c.execute(
                text(
                    "SELECT active_streams FROM artifacts.capacity WHERE tenant_id=:tenant AND project_id=:project"
                ),
                e.p.bindings,
            ).scalar_one()
            == 0
        )


def test_live_writer_lock_defers_expired_recovery(flow):
    e = flow
    prefix = stopped_at_upload(e)
    e.uploads.limits = replace(e.uploads.limits, seconds=1)
    attempt = e.uploads.start(e.p, prefix.upload_id)
    writer = e.storage.writer(attempt)
    try:
        with e.engine.connect() as c:
            c.execute(text("SELECT pg_sleep(1.05)"))
        assert encode(e).outcome.state == "pending"
        assert not e.storage.sidecar(attempt.storage_key, ".retired").exists()
    finally:
        writer.close()
    assert encode(e).outcome.state == "published"


def test_exhausted_upload_gets_terminal_proof_before_numbered_retry(flow):
    e = flow
    prefix = stopped_at_upload(e)
    e.uploads.limits = replace(e.uploads.limits, attempts=1)
    attempt = e.uploads.start(e.p, prefix.upload_id)
    e.uploads.finish(e.p, attempt, verified=False, actual_bytes=0)
    with pytest.raises(UploadError):
        encode(e)
    assert encode(e).outcome.state == "published"
    with e.engine.connect() as c:
        attempts = (
            c.execute(
                text(
                    "SELECT DISTINCT attempt FROM artifacts.encoding_binding_events WHERE tenant_id=:tenant AND project_id=:project ORDER BY attempt"
                ),
                e.p.bindings,
            )
            .scalars()
            .all()
        )
        assert attempts == [1, 2]


def test_revocation_preserves_published_replay_but_blocks_new_alias(flow):
    e = flow
    result = encode(e)
    prior = e.e.e.workflow.rights.history(e.p, e.e.source.rights.rights_id, 1)
    denied = prior.model_copy(
        update={
            "reference": prior.reference.model_copy(update={"revision": 2}),
            "supersedes": prior.reference,
            "status": "revoked",
            "allowed_uses": (),
        }
    )
    e.e.e.workflow.rights.publish(e.p, denied)
    assert encode(e) == result
    with pytest.raises(RightsError):
        e.workflow.encode(e.p, e.request.model_copy(update={"encoding_id": "new"}))


def test_abandoned_upload_uses_actual_final_rejection_then_recovers(flow):
    from amphora_data_artifacts.maintenance.cleanup import Cleanup

    e = flow
    prefix = stopped_at_upload(e)
    with e.engine.connect() as c:
        c.execute(text("SELECT pg_sleep(1.05)"))
    Cleanup(e.uploads, e.storage, grace_seconds=1).sweep(replace(e.p, actions=e.p.actions | {"cleanup"}))
    assert e.workflow.streams.inspect(e.p, prefix.upload_id).status == "abandoned"
    with pytest.raises(UploadError):
        encode(e)
    assert encode(e).outcome.state == "published"


def test_rejected_begin_is_visible_error_then_new_attempt_can_progress(flow):
    e = flow
    allowed = e.uploads.policy
    e.uploads.policy = ContentPolicy(frozenset())
    with pytest.raises(UploadError):
        encode(e)
    e.uploads.policy = allowed
    assert encode(e).outcome.state == "published"


def test_pending_upload_cannot_be_reclassified_as_exhausted(flow):
    e = flow
    prefix = stopped_at_upload(e)
    lease = e.workflow.claims.claim(e.p, prefix.publication.identity.binding_id)
    try:
        with pytest.raises(RepresentationError, match="upload_recoverable"):
            e.workflow.journal.prepare_unavailable_upload(e.p, lease, e.uploads.limits)
        assert not e.workflow.streams.settle_expired(e.p, prefix.upload_id)
        with pytest.raises(UploadError, match="upload_unavailable"):
            e.workflow.streams.inspect(replace(e.p, actor_id="other"), prefix.upload_id)
    finally:
        e.workflow.claims.release(e.p, lease)
