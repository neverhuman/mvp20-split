"""Actual Data/PG authority using a test-only projection port; no Qdrant claim."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_data_artifacts.retrieval.lifecycle import GenerationPhase
from amphora_data_artifacts.retrieval.proof_records import head
from amphora_data_artifacts.retrieval.publication import GenerationPublication
from amphora_data_artifacts.retrieval.validation import RetrievalError
from amphora_data_artifacts.source_rights.ledger import SourceRights
from amphora_data_artifacts.source_rights.model import RightsError
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

pytestmark = pytest.mark.postgres


def rows(e, table):
    with e.engine.connect() as c:
        return c.execute(
            text(
                "SELECT count(*) FROM artifacts." + table + " WHERE tenant_id=:tenant AND project_id=:project"
            ),
            e.p.bindings,
        ).scalar_one()


def expire(e):
    with e.engine.begin() as c:
        c.execute(
            text(
                "UPDATE artifacts.index_generation_cursors SET expires_at=clock_timestamp()-interval '1 second' WHERE tenant_id=:tenant AND project_id=:project"
            ),
            e.p.bindings,
        )


def revoke(e):
    rights = SourceRights(e.engine)
    old = rights.history(e.p, e.source.rights.rights_id, 1)
    rights.publish(
        e.p,
        old.model_copy(
            update={
                "reference": old.reference.model_copy(update={"revision": 2}),
                "supersedes": old.reference,
                "status": "revoked",
                "allowed_uses": (),
            }
        ),
    )


def test_owned_bytes_verified_then_published_and_reconstructed_without_backend_io(projection):
    e = projection
    with pytest.raises(RetrievalError, match="not_verified"):
        e.publication.publish(e.p, e.lease)
    proof = e.publication.build_and_verify(e.p, e.lease)
    snapshot = e.backend_port.snapshots[e.lease.attempt.namespace]
    assert snapshot.dimensions == 16 and snapshot.metric == "dot"
    assert snapshot.points[0].values == (0.0, 2.0, 2.0) + (0.0,) * 13
    assert snapshot.points[1].values == (0.0, 1.0, 1.0) + (0.0,) * 13
    assert proof.point_count == 2 and rows(e, "index_verifications") == 1
    same = GenerationPublication(e.ingestion.reads, e.backend_port)
    calls = list(e.backend_port.calls)
    assert same.build_and_verify(e.p, e.lease) == proof
    assert e.backend_port.calls == calls
    result = same.publish(e.p, e.lease)
    assert result.state == "published"
    with e.engine.connect() as c:
        assert head(c, e.p, "corpus") == e.lease.attempt.generation
    revoke(e)
    assert same.publish(e.p, e.lease) == result
    assert e.backend_port.calls == calls
    assert rows(e, "index_publications") == rows(e, "index_heads") == 1


@pytest.mark.parametrize(
    "mutation,reason",
    [
        (lambda s: replace(s, points=()), "count"),
        (lambda s: replace(s, points=s.points + (s.points[0],)), "count"),
        (lambda s: replace(s, points=(s.points[0], s.points[0])), "duplicate"),
        (lambda s: replace(s, dimensions=17), "space"),
        (lambda s: replace(s, metric="euclidean"), "space"),
        (
            lambda s: replace(
                s, points=(replace(s.points[0], point_id="00000000-0000-0000-0000-000000000000"), s.points[1])
            ),
            "missing",
        ),
        (lambda s: replace(s, points=(replace(s.points[0], values=(0.0,) * 16), s.points[1])), "content"),
        (
            lambda s: replace(
                s,
                points=(
                    replace(s.points[0], profile=s.points[0].profile.model_copy(update={"sha256": "0" * 64})),
                    s.points[1],
                ),
            ),
            "content",
        ),
        (
            lambda s: replace(s, points=(replace(s.points[0], binding=s.points[1].binding), s.points[1])),
            "content",
        ),
    ],
)
def test_actual_observation_must_match_every_expected_point(projection, mutation, reason):
    e = projection
    e.backend_port.transform = mutation
    with pytest.raises(RetrievalError, match="projection_" + reason):
        e.publication.build_and_verify(e.p, e.lease)
    assert rows(e, "index_verifications") == rows(e, "index_publications") == 0
    assert e.intents.read(e.p, "corpus", "g1").state == "building"


def test_observation_order_does_not_change_manifest_identity(projection):
    e = projection
    e.backend_port.transform = lambda s: replace(s, points=tuple(reversed(s.points)))
    assert e.publication.build_and_verify(e.p, e.lease).point_count == 2
    assert e.publication.publish(e.p, e.lease).state == "published"


def test_revocation_during_external_effect_prevents_verification(projection):
    e = projection
    e.backend_port.after_build = lambda: revoke(e)
    with pytest.raises(RightsError):
        e.publication.build_and_verify(e.p, e.lease)
    assert rows(e, "index_verifications") == rows(e, "index_publications") == 0
    assert e.lease.attempt.namespace in e.backend_port.snapshots
    assert e.leases.finish(e.p, e.lease, GenerationPhase.ABANDONED, "revoked").state == "abandoned"


def test_takeover_during_external_effect_cannot_reuse_old_projection(projection):
    e = projection
    claims = []

    def takeover():
        expire(e)
        claims.append(e.leases.claim(e.p, "corpus", "g1"))

    e.backend_port.after_build = takeover
    with pytest.raises(RetrievalError, match="stale_claim"):
        e.publication.build_and_verify(e.p, e.lease)
    new = claims[0]
    assert new.attempt.namespace != e.lease.attempt.namespace
    assert rows(e, "index_verifications") == 0
    e.backend_port.after_build = lambda: None
    assert e.publication.build_and_verify(e.p, new).attempt == new.attempt
    assert e.publication.publish(e.p, new).state == "published"
    assert len(e.backend_port.snapshots) == 2


def test_verified_expiry_is_terminal_even_after_rights_revocation(projection):
    e = projection
    e.publication.build_and_verify(e.p, e.lease)
    expire(e)
    revoke(e)
    assert e.leases.claim(e.p, "corpus", "g1").state == "failed"
    assert rows(e, "index_verifications") == 1
    assert rows(e, "index_publications") == 0


def test_current_rights_rechecked_at_publication(projection):
    e = projection
    e.publication.build_and_verify(e.p, e.lease)
    revoke(e)
    with pytest.raises(RightsError):
        e.publication.publish(e.p, e.lease)
    assert rows(e, "index_publications") == rows(e, "index_heads") == 0


def test_competing_heads_have_one_winner_then_exact_historical_replay(projection):
    e = projection
    e.publication.build_and_verify(e.p, e.lease)
    e.intents.prepare(e.p, e.request.model_copy(update={"generation_id": "g2"}))
    second = e.leases.claim(e.p, "corpus", "g2")
    e.publication.build_and_verify(e.p, second)

    def publish(lease):
        try:
            return e.publication.publish(e.p, lease)
        except RetrievalError as error:
            assert str(error) == "retrieval_head_conflict"
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(publish, (e.lease, second)))
    assert sum(x is not None for x in outcomes) == 1
    old_lease = e.lease if outcomes[0] is not None else second
    old_result = next(x for x in outcomes if x is not None)
    assert rows(e, "index_publications") == 1
    request = e.request.model_copy(
        update={"generation_id": "g3", "expected_head": old_result.generation.reference}
    )
    e.intents.prepare(e.p, request)
    third = e.leases.claim(e.p, "corpus", "g3")
    e.publication.build_and_verify(e.p, third)
    assert e.publication.publish(e.p, third).state == "published"
    assert e.publication.publish(e.p, old_lease) == old_result
    with e.engine.connect() as c:
        assert head(c, e.p, "corpus") == third.attempt.generation
    assert rows(e, "index_publications") == 2


def test_backend_identity_and_immutable_proof_guards(projection):
    e = projection
    original = e.backend_port.reference
    e.backend_port.reference = original.model_copy(update={"sha256": "b" * 64})
    with pytest.raises(RetrievalError, match="backend_profile"):
        e.publication.build_and_verify(e.p, e.lease)
    assert not e.backend_port.calls
    e.backend_port.reference = original
    e.publication.build_and_verify(e.p, e.lease)
    e.publication.publish(e.p, e.lease)
    for table in ("index_verifications", "index_publications"):
        for command in (
            "UPDATE artifacts." + table + " SET tenant_id=tenant_id",
            "DELETE FROM artifacts." + table,
        ):
            with pytest.raises(ProgrammingError), e.engine.begin() as c:
                c.execute(text(command + " WHERE tenant_id=:tenant AND project_id=:project"), e.p.bindings)


def test_two_verifiers_of_same_live_attempt_commit_one_proof(projection):
    from threading import Barrier

    e = projection
    barrier = Barrier(2, timeout=10)
    e.backend_port.after_build = barrier.wait
    with ThreadPoolExecutor(max_workers=2) as pool:
        proofs = list(pool.map(lambda _: e.publication.build_and_verify(e.p, e.lease), range(2)))
    assert proofs[0] == proofs[1]
    assert rows(e, "index_verifications") == 1
    with e.engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM artifacts.index_generation_events WHERE tenant_id=:tenant AND project_id=:project AND phase='verified'"
                ),
                e.p.bindings,
            ).scalar_one()
            == 1
        )
    assert e.publication.publish(e.p, e.lease).state == "published"


@pytest.mark.parametrize("stage", ["build", "inspect"])
def test_backend_uncertainty_never_grants_verification(projection, monkeypatch, stage):
    e = projection

    def unavailable(*args):
        raise TimeoutError("test-only backend interruption")

    with monkeypatch.context() as patch:
        patch.setattr(e.backend_port, stage, unavailable)
        with pytest.raises(TimeoutError):
            e.publication.build_and_verify(e.p, e.lease)
    assert rows(e, "index_verifications") == rows(e, "index_publications") == 0
    assert e.intents.read(e.p, "corpus", "g1").state == "building"
    assert e.publication.build_and_verify(e.p, e.lease).attempt == e.lease.attempt
    assert e.publication.publish(e.p, e.lease).state == "published"
