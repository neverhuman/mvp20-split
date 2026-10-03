"""Actual PostgreSQL generation admission/history and competing fenced claims."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_data_artifacts.publication.model import UploadError
from amphora_data_artifacts.representations.validation import RepresentationError
from amphora_data_artifacts.retrieval.intents import GenerationIntents
from amphora_data_artifacts.retrieval.leases import GenerationBusy, GenerationLease
from amphora_data_artifacts.retrieval.lifecycle import GenerationPhase
from amphora_data_artifacts.retrieval.validation import RetrievalError
from amphora_data_artifacts.source_rights.ledger import SourceRights
from amphora_data_artifacts.source_rights.model import RightsError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

pytestmark = pytest.mark.postgres


def expire(e):
    with e.engine.begin() as c:
        c.execute(text("UPDATE artifacts.index_generation_cursors SET expires_at=clock_timestamp()-interval '1 second' WHERE tenant_id=:tenant AND project_id=:project"), e.p.bindings)


def revoke(e):
    rights = SourceRights(e.engine)
    old = rights.history(e.p, e.source.rights.rights_id, 1)
    new = old.model_copy(update={"reference": old.reference.model_copy(update={"revision": 2}),
        "supersedes": old.reference, "status": "revoked", "allowed_uses": ()})
    rights.publish(e.p, new)


def test_admission_exact_reconstruction_conflicts_and_actor_scope(generation):
    e = generation
    first = e.intents.prepare(e.p, e.request)
    assert first.state == "prepared"
    assert first.generation.manifest.bindings == (e.binding,)
    assert GenerationIntents(e.engine, e.backend).prepare(e.p, e.request) == first
    assert e.intents.read(e.p, "corpus", "g1") == first
    conflicting = GenerationIntents(e.engine, e.backend.model_copy(update={"sha256": "b" * 64}))
    with pytest.raises(RetrievalError, match="generation_conflict"):
        conflicting.prepare(e.p, e.request)
    with pytest.raises(RetrievalError, match="generation_missing"):
        e.intents.read(replace(e.p, actor_id="other"), "corpus", "g1")
    with pytest.raises(RetrievalError, match="generation_missing"):
        e.intents.read(replace(e.p, scope=e.p.scope.model_copy(update={"project_id": "missing"})), "corpus", "g1")
    with pytest.raises(UploadError):
        e.intents.prepare(replace(e.p, actions=frozenset()), e.request)


def test_unresolved_or_forged_binding_cannot_leave_intent(generation):
    e = generation
    for ref, reason in ((e.binding.reference.model_copy(update={"binding_id": "missing"}), "binding_missing"),
                        (e.binding.reference.model_copy(update={"sha256": "0" * 64}), "request_bindings")):
        with pytest.raises(RetrievalError, match=reason):
            e.intents.prepare(e.p, e.request.model_copy(update={"bindings": (ref,)}))
    with e.engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM artifacts.index_generations WHERE tenant_id=:tenant AND project_id=:project"), e.p.bindings).scalar_one() == 0
    foreign = e.request.profile.model_copy(update={"scope": e.p.scope.model_copy(update={"project_id": "foreign"})})
    with pytest.raises(RepresentationError, match="scope"):
        e.intents.prepare(e.p, e.request.model_copy(update={"profile": foreign}))


def test_current_processing_rights_gate_new_work_but_not_exact_history(generation):
    e = generation
    original = e.intents.prepare(e.p, e.request)
    lease = e.leases.claim(e.p, "corpus", "g1")
    revoke(e)
    assert e.intents.prepare(e.p, e.request).generation == original.generation
    assert e.intents.read(e.p, "corpus", "g1").state == "building"
    with pytest.raises(RightsError):
        e.intents.prepare(e.p, e.request.model_copy(update={"generation_id": "g2"}))
    with pytest.raises(RightsError):
        e.leases.renew(e.p, lease)
    with pytest.raises(RightsError):
        e.leases.claim(e.p, "corpus", "g1")
    assert e.leases.finish(e.p, lease, GenerationPhase.ABANDONED, "rights_revoked").state == "abandoned"


def test_concurrent_claims_single_winner_and_expired_takeover(generation):
    e = generation
    e.intents.prepare(e.p, e.request)
    with ThreadPoolExecutor(max_workers=4) as pool:
        claims = list(pool.map(lambda _: e.leases.claim(e.p, "corpus", "g1"), range(4)))
    winners = [x for x in claims if isinstance(x, GenerationLease)]
    assert len(winners) == 1
    assert sum(isinstance(x, GenerationBusy) for x in claims) == 3
    old = winners[0]
    renewed = e.leases.renew(e.p, old)
    assert renewed.attempt == old.attempt and renewed.expires_at >= old.expires_at
    expire(e)
    new = e.leases.claim(e.p, "corpus", "g1")
    assert new.attempt.fence == old.attempt.fence + 1
    assert new.attempt.namespace != old.attempt.namespace
    for action in (lambda: e.leases.renew(e.p, old),
                   lambda: e.leases.finish(e.p, old, GenerationPhase.FAILED, "stale")):
        with pytest.raises(RetrievalError, match="stale_claim"):
            action()
    assert e.leases.finish(e.p, new, GenerationPhase.FAILED, "fixture_failure").state == "failed"
    assert e.leases.claim(e.p, "corpus", "g1").state == "failed"
    with pytest.raises(RetrievalError, match="terminal"):
        e.leases.renew(e.p, new)
    with e.engine.connect() as c:
        namespaces = c.execute(text("SELECT namespace FROM artifacts.index_build_attempts WHERE tenant_id=:tenant AND project_id=:project ORDER BY fence"),e.p.bindings).scalars().all()
        phases = c.execute(text("SELECT phase FROM artifacts.index_generation_events WHERE tenant_id=:tenant AND project_id=:project ORDER BY sequence"),e.p.bindings).scalars().all()
    assert namespaces == [old.attempt.namespace, new.attempt.namespace]
    assert phases == ["prepared", "building", "building", "failed"]


def test_no_claim_can_assert_verified_or_published_and_prepared_abandon(generation):
    e = generation
    e.intents.prepare(e.p, e.request)
    assert e.leases.abandon_prepared(e.p, "corpus", "g1").state == "abandoned"
    assert e.leases.claim(e.p, "corpus", "g1").state == "abandoned"
    with pytest.raises(RetrievalError, match="not_prepared"):
        e.leases.abandon_prepared(e.p, "corpus", "g1")
    e.intents.prepare(e.p, e.request.model_copy(update={"generation_id": "g2"}))
    lease = e.leases.claim(e.p, "corpus", "g2")
    for phase in (GenerationPhase.VERIFIED, GenerationPhase.PUBLISHED, "failed"):
        with pytest.raises(RetrievalError, match="terminal_required"):
            e.leases.finish(e.p, lease, phase, "untrusted")
    with pytest.raises(RetrievalError, match="generation_missing"):
        e.leases.renew(replace(e.p, actor_id="other"), lease)
    with pytest.raises(RetrievalError, match="claim_scope"):
        e.leases.renew(replace(e.p, scope=e.p.scope.model_copy(update={"project_id": "other"})), lease)


def test_immutable_history_grants_and_membership_foreign_keys(generation):
    e = generation
    e.intents.prepare(e.p, e.request)
    e.leases.claim(e.p, "corpus", "g1")
    for table in ("index_generations", "index_generation_bindings", "index_build_attempts", "index_generation_events"):
        for operation in ("UPDATE artifacts." + table + " SET tenant_id=tenant_id", "DELETE FROM artifacts." + table):
            with pytest.raises(ProgrammingError), e.engine.begin() as c:
                c.execute(text(operation + " WHERE tenant_id=:tenant AND project_id=:project"), e.p.bindings)
    with pytest.raises(ProgrammingError), e.engine.begin() as c:
        c.execute(text("UPDATE artifacts.index_generation_cursors SET generation_id='other' WHERE tenant_id=:tenant AND project_id=:project"),e.p.bindings)
    with pytest.raises(IntegrityError), e.engine.begin() as c:
        c.execute(text("INSERT INTO artifacts.index_generation_bindings (tenant_id,project_id,corpus_id,generation_id,ordinal,binding_id) VALUES (:tenant,:project,'corpus','g1',1,'missing')"),e.p.bindings)


def test_lease_expiring_during_rights_check_cannot_be_renewed(generation, monkeypatch):
    import amphora_data_artifacts.retrieval.leases as module
    from amphora_data_artifacts.representations.storage.claims import LeasePolicy

    e = generation
    e.intents.prepare(e.p, e.request)
    leases = module.GenerationLeases(e.engine, LeasePolicy(1))
    lease = leases.claim(e.p, "corpus", "g1")
    original = module.authorize_plan

    def delayed(connection, principal, plan):
        result = original(connection, principal, plan)
        connection.execute(text("SELECT pg_sleep(1.1)"))
        return result

    with monkeypatch.context() as patch:
        patch.setattr(module, "authorize_plan", delayed)
        with pytest.raises(RetrievalError, match="stale_claim"):
            leases.renew(e.p, lease)
    next_claim = leases.claim(e.p, "corpus", "g1")
    assert next_claim.attempt.fence == lease.attempt.fence + 1
