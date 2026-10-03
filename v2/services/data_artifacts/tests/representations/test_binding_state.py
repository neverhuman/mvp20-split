"""Actual owner journals, request convergence, fenced recovery and retained rejection proof."""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_contracts_representations import representation_vector_schema
from amphora_data_artifacts.derivations.publication import DerivedPublications
from amphora_data_artifacts.persistence.commands import CommandStore
from amphora_data_artifacts.publication.finalize import Finalizer
from amphora_data_artifacts.publication.model import ContentPolicy, UploadError
from amphora_data_artifacts.representations.bindings.content_rule import VectorContentRule
from amphora_data_artifacts.representations.bindings.journal import BindingJournal
from amphora_data_artifacts.representations.bindings.leases import BindingBusy, BindingLease, BindingLeases
from amphora_data_artifacts.representations.bindings.requests import BindingRequests
from amphora_data_artifacts.representations.fixture import FixtureEncoder
from amphora_data_artifacts.representations.payloads import EncodedRepresentation
from amphora_data_artifacts.representations.storage.claims import LeasePolicy
from amphora_data_artifacts.representations.storage.leases import WorkLeases
from amphora_data_artifacts.representations.storage.results import EncodingResults
from amphora_data_artifacts.representations.validation import RepresentationError
from amphora_data_artifacts.source_rights.model import RightsError
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

pytestmark = pytest.mark.postgres


@pytest.fixture
def state(source_setup):
    e = source_setup
    p = replace(e.principal, actions=e.principal.actions | {"upload", "finalize"})
    prepared = e.preflight.load(p, e.request)
    engine = e.e.env.engine
    requests = BindingRequests(engine)
    assert requests.register(p, e.request, prepared).outcome.state == "pending"
    compute = WorkLeases(engine).claim(p, e.ref, prepared.input)
    result = EncodedRepresentation.prepare(
        e.profile, prepared.input, FixtureEncoder().encode(e.profile, prepared.input)
    )
    EncodingResults(engine).complete(p, compute, result)
    uploads = e.e.env.uploads
    schema = representation_vector_schema()
    policy = uploads.policy
    uploads.policy = ContentPolicy(
        policy.allowed | {("application/json", schema.schema_id, schema.version, schema.sha256)},
        rules=policy.rules + (VectorContentRule(),),
    )
    return SimpleNamespace(
        e=e,
        p=p,
        prepared=prepared,
        engine=engine,
        requests=requests,
        claims=BindingLeases(engine),
        journal=BindingJournal(engine),
        uploads=uploads,
        derived=DerivedPublications(uploads),
        finalizer=Finalizer(uploads, e.e.env.storage),
    )


def claim(s):
    return s.claims.claim(s.p, s.prepared.identity.binding_id)


def stream(s, lease):
    prefix = s.journal.read(s.p, lease)
    attempt = s.uploads.start(s.p, prefix.upload_id)
    writer = s.e.e.env.storage.writer(attempt)
    try:
        writer.write(prefix.publication.payload)
        writer.seal()
    finally:
        writer.close()
    assert (
        s.uploads.finish(s.p, attempt, verified=True, actual_bytes=len(prefix.publication.payload))
        == "streamed"
    )


def test_alias_identity_actor_isolation_and_conflict_rollback(state):
    s = state
    alias = s.e.request.model_copy(update={"encoding_id": "alias"})
    assert s.requests.register(s.p, alias, s.prepared).request == alias
    with s.engine.connect() as c:
        count = c.execute(
            text(
                "SELECT count(*) FROM artifacts.encoding_binding_jobs WHERE tenant_id=:tenant AND project_id=:project"
            ),
            s.p.bindings,
        ).scalar_one()
        assert count == 1
    wrong = s.e.request.model_copy(update={"source": s.e.request.source.model_copy(update={"start": 8})})
    with pytest.raises(RepresentationError, match="prepared_identity"):
        s.requests.register(s.p, wrong, s.prepared)
    assert s.requests.read(replace(s.p, actor_id="other"), alias.encoding_id) is None
    assert BindingRequests(s.engine).read(s.p, alias.encoding_id).request == alias
    with pytest.raises(RepresentationError, match="binding_missing"):
        s.claims.claim(replace(s.p, actor_id="other"), s.prepared.identity.binding_id)


def test_competing_claims_expiry_renewal_and_stale_fences(state):
    s = state
    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(lambda _: claim(s), range(4)))
    leases = [x for x in outcomes if isinstance(x, BindingLease)]
    assert len(leases) == 1 and sum(isinstance(x, BindingBusy) for x in outcomes) == 3
    first = leases[0]
    renewed = s.claims.renew(s.p, first)
    assert renewed.fence == first.fence and renewed.expires_at >= first.expires_at
    assert s.claims.release(s.p, renewed)
    assert not s.claims.release(s.p, renewed)
    second = claim(s)
    assert second.fence == first.fence + 1 and second.token != first.token
    with pytest.raises(RepresentationError, match="stale_claim"):
        s.journal.prepare(s.p, first, "begin")
    with pytest.raises(RepresentationError, match="claim_actor"):
        s.claims.renew(replace(s.p, actor_id="other"), second)
    s.claims.release(s.p, second)
    short = BindingLeases(s.engine, LeasePolicy(1))
    expiring = short.claim(s.p, s.prepared.identity.binding_id)
    with s.engine.connect() as c:
        c.execute(text("SELECT pg_sleep(1.05)"))
    with pytest.raises(RepresentationError, match="stale_claim"):
        short.renew(s.p, expiring)
    assert not short.release(s.p, expiring)


def test_retained_prefix_reconstructs_actual_artifact_and_published_aliases(state):
    s = state
    lease = claim(s)
    begin = s.journal.prepare(s.p, lease, "begin")
    assert CommandStore(s.engine).inspect(begin) is None
    assert not s.journal.observe(s.p, lease, "begin")
    assert s.journal.prepare(s.p, lease, "begin") == begin
    s.derived.begin(s.p, begin)
    # Simulate lost response before journal acknowledgement with fresh owner objects/claim.
    s.claims.release(s.p, lease)
    lease = BindingLeases(s.engine).claim(s.p, s.prepared.identity.binding_id)
    journal = BindingJournal(s.engine)
    assert journal.read(s.p, lease).command("begin") == begin
    assert journal.observe(s.p, lease, "begin")
    assert not journal.streamed(s.p, lease)
    with pytest.raises(RepresentationError, match="publication_order"):
        journal.prepare(s.p, lease, "finalize")
    stream(s, lease)
    assert journal.streamed(s.p, lease)
    final = journal.prepare(s.p, lease, "finalize")
    assert journal.prepare(s.p, lease, "finalize") == final
    receipt = s.finalizer.finalize(s.p, final)
    assert journal.observe(s.p, lease, "finalize")
    binding = journal.publish(s.p, lease)
    assert binding.vector == receipt.artifact
    assert s.requests.read(s.p, s.e.request.encoding_id).outcome.binding == binding
    assert claim(s) == binding
    with pytest.raises(RepresentationError, match="binding_complete"):
        s.claims.renew(s.p, lease)
    alias = s.e.request.model_copy(update={"encoding_id": "after-publication"})
    assert s.requests.register(s.p, alias, s.e.preflight.load(s.p, alias)).outcome.binding == binding


def test_pending_command_cannot_authorize_retry_but_actual_rejection_can(state):
    s = state
    lease = claim(s)
    begin = s.journal.prepare(s.p, lease, "begin")
    CommandStore(s.engine).register(begin)
    assert not s.journal.observe(s.p, lease, "begin")
    with pytest.raises(RepresentationError, match="retry_unproven"):
        s.journal.retry(s.p, lease)
    allowed = s.uploads.policy
    s.uploads.policy = ContentPolicy(frozenset())
    with pytest.raises(UploadError):
        s.derived.begin(s.p, begin)
    assert s.journal.observe(s.p, lease, "begin")
    assert s.journal.read(s.p, lease).stage == "rejected"
    assert s.journal.retry(s.p, lease) == 2
    second = s.journal.prepare(s.p, lease, "begin")
    assert second.identity.command_id == begin.identity.command_id + ".a2"
    s.uploads.policy = allowed
    s.derived.begin(s.p, second)
    assert s.journal.observe(s.p, lease, "begin")


def test_rights_revocation_blocks_admission_claim_and_journal_but_preserves_status(state):
    s = state
    lease = claim(s)
    prior = s.e.e.workflow.rights.history(s.p, s.e.source.rights.rights_id, 1)
    revised = prior.model_copy(
        update={
            "reference": prior.reference.model_copy(update={"revision": 2}),
            "supersedes": prior.reference,
            "status": "revoked",
            "allowed_uses": (),
        }
    )
    s.e.e.workflow.rights.publish(s.p, revised)
    assert s.requests.read(s.p, s.e.request.encoding_id).outcome.state == "pending"
    with pytest.raises(RightsError):
        s.requests.register(s.p, s.e.request, s.prepared)
    with pytest.raises(RightsError):
        claim(s)
    with pytest.raises(RightsError):
        s.journal.prepare(s.p, lease, "begin")


def test_immutable_rows_and_narrow_cursor_privileges(state):
    s = state
    claim(s)
    for table in (
        "encoding_binding_jobs",
        "encoding_requests",
        "encoding_binding_events",
        "representation_bindings",
    ):
        with s.engine.connect() as c:
            with pytest.raises(ProgrammingError):
                c.execute(
                    text(
                        "DELETE FROM artifacts." + table + " WHERE tenant_id=:tenant AND project_id=:project"
                    ),
                    s.p.bindings,
                )
            c.rollback()
    with s.engine.connect() as c:
        with pytest.raises(ProgrammingError):
            c.execute(
                text(
                    "UPDATE artifacts.encoding_binding_cursors SET binding_id='bad' WHERE tenant_id=:tenant AND project_id=:project"
                ),
                s.p.bindings,
            )
        c.rollback()


def test_final_rejection_retries_without_rewriting_prior_attempt(state):
    s = state
    lease = claim(s)
    begin = s.journal.prepare(s.p, lease, "begin")
    s.derived.begin(s.p, begin)
    s.journal.observe(s.p, lease, "begin")
    stream(s, lease)
    s.journal.streamed(s.p, lease)
    final = s.journal.prepare(s.p, lease, "finalize")
    # A later upload generation makes the retained streamed observation stale.
    stale = s.uploads.start(s.p, s.journal.read(s.p, lease).upload_id)
    s.uploads.finish(s.p, stale, verified=False, actual_bytes=0)
    with pytest.raises(UploadError):
        s.finalizer.finalize(s.p, final)
    assert s.journal.observe(s.p, lease, "finalize")
    assert s.journal.retry(s.p, lease) == 2
    assert CommandStore(s.engine).inspect(final).status == "rejected"
    second = s.journal.prepare(s.p, lease, "begin")
    assert s.derived.begin(s.p, second).upload.upload_id != s.derived.begin(s.p, begin).upload.upload_id


def test_post_finalization_revocation_prevents_new_binding_visibility(state):
    s = state
    lease = claim(s)
    s.derived.begin(s.p, s.journal.prepare(s.p, lease, "begin"))
    s.journal.observe(s.p, lease, "begin")
    stream(s, lease)
    s.journal.streamed(s.p, lease)
    s.finalizer.finalize(s.p, s.journal.prepare(s.p, lease, "finalize"))
    s.journal.observe(s.p, lease, "finalize")
    prior = s.e.e.workflow.rights.history(s.p, s.e.source.rights.rights_id, 1)
    denied = prior.model_copy(
        update={
            "reference": prior.reference.model_copy(update={"revision": 2}),
            "supersedes": prior.reference,
            "status": "revoked",
            "allowed_uses": (),
        }
    )
    s.e.e.workflow.rights.publish(s.p, denied)
    with pytest.raises(RightsError):
        s.journal.publish(s.p, lease)
    assert s.requests.read(s.p, s.e.request.encoding_id).outcome.state == "pending"
    restored = prior.model_copy(
        update={
            "reference": prior.reference.model_copy(update={"revision": 3}),
            "supersedes": denied.reference,
        }
    )
    s.e.e.workflow.rights.publish(s.p, restored)
    binding = s.journal.publish(s.p, lease)
    denied_again = denied.model_copy(
        update={
            "reference": prior.reference.model_copy(update={"revision": 4}),
            "supersedes": restored.reference,
        }
    )
    s.e.e.workflow.rights.publish(s.p, denied_again)
    assert s.requests.read(s.p, s.e.request.encoding_id).outcome.binding == binding
    with pytest.raises(RightsError):
        s.e.e.reads.content(s.p, binding.vector.artifact_id)


def test_real_request_identity_conflict_rolls_back_new_job(state):
    s = state
    span = s.e.request.source.model_copy(
        update={"start": 0, "end": 6, "sha256": hashlib.sha256(b"prefix").hexdigest()}
    )
    request = s.e.request.model_copy(update={"source": span})
    prepared = s.e.preflight.load(s.p, request)
    with pytest.raises(RepresentationError, match="request_conflict"):
        s.requests.register(s.p, request, prepared)
    with pytest.raises(RepresentationError, match="binding_missing"):
        s.claims.claim(s.p, prepared.identity.binding_id)
    assert s.requests.read(s.p, request.encoding_id).request == s.e.request


def test_missing_result_does_not_advance_journal_and_claim_bounds(state):
    s = state
    from datetime import datetime

    span = s.e.request.source.model_copy(
        update={"start": 0, "end": 6, "sha256": hashlib.sha256(b"prefix").hexdigest()}
    )
    request = s.e.request.model_copy(update={"encoding_id": "uncached", "source": span})
    prepared = s.e.preflight.load(s.p, request)
    s.requests.register(s.p, request, prepared)
    lease = s.claims.claim(s.p, prepared.identity.binding_id)
    with pytest.raises(RepresentationError, match="result_pending"):
        s.journal.prepare(s.p, lease, "begin")
    for fields, code in (
        ({"fence": True}, "fence_bound"),
        ({"expires_at": datetime(2026, 1, 1)}, "lease_time"),
    ):
        with pytest.raises(RepresentationError, match=code):
            replace(lease, **fields)
    with pytest.raises(RepresentationError, match="lease_policy"):
        BindingLeases(s.engine, 5)
    assert s.requests.read(s.p, "absent") is None
