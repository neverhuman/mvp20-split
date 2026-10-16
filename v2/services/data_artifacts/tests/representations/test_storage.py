"""Real private PostgreSQL cache semantics; source publication/rights remain separate."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime
from threading import Barrier
from types import SimpleNamespace

import pytest
from amphora_contracts_core import Scope
from amphora_data_artifacts.persistence.migrate import upgrade
from amphora_data_artifacts.publication.model import Principal, UploadError
from amphora_data_artifacts.representations.fixture import FixtureEncoder, fixture_profile
from amphora_data_artifacts.representations.identity import EncodingInput, EncodingWorkIdentity
from amphora_data_artifacts.representations.payloads import EncodedRepresentation
from amphora_data_artifacts.representations.storage.claims import CacheHit, LeasePolicy, WorkBusy, WorkLease
from amphora_data_artifacts.representations.storage.leases import WorkLeases
from amphora_data_artifacts.representations.storage.registry import ProfileRegistry
from amphora_data_artifacts.representations.storage.results import EncodingResults
from amphora_data_artifacts.representations.validation import RepresentationError
from amphora_data_artifacts.representations.vectors import Float32Vector
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


@pytest.fixture
def cache(artifact_database):
    engine = create_engine(artifact_database, connect_args={"options": "-c statement_timeout=5000"})
    principal = Principal(
        "owner",
        Scope(tenant_id="representations", project_id=uuid.uuid4().hex),
        frozenset({"representation_manage", "representation_read", "representation_encode"}),
    )
    registry = ProfileRegistry(engine)
    profile = fixture_profile()
    ref = registry.register(principal, profile)
    source = EncodingInput(b"ABBA")
    result = EncodedRepresentation.prepare(profile, source, FixtureEncoder().encode(profile, source))
    try:
        yield SimpleNamespace(
            engine=engine,
            principal=principal,
            registry=registry,
            profile=profile,
            ref=ref,
            source=source,
            result=result,
            leases=WorkLeases(engine),
            results=EncodingResults(engine),
        )
    finally:
        engine.dispose()


def expire(e, lease):
    with e.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE artifacts.encoding_leases SET expires_at=clock_timestamp()-interval '1 second' "
                "WHERE tenant_id=:tenant AND project_id=:project AND work_sha256=:work"
            ),
            e.principal.bindings | {"work": lease.work.sha256},
        )


def test_registry_replay_conflict_scope_digest_and_grants(cache):
    e = cache
    assert e.registry.register(e.principal, e.profile) == e.ref
    assert ProfileRegistry(e.engine).read(e.principal, e.ref) == e.profile
    with pytest.raises(RepresentationError, match="profile_conflict"):
        e.registry.register(e.principal, replace(e.profile, limitations=("changed",)))
    with pytest.raises(RepresentationError, match="profile_conflict"):
        e.registry.read(e.principal, e.ref.model_copy(update={"sha256": "a" * 64}))
    with pytest.raises(RepresentationError, match="profile_missing"):
        e.registry.read(e.principal, e.ref.model_copy(update={"profile_id": "missing"}))
    with pytest.raises(RepresentationError, match="scope"):
        e.registry.read(replace(e.principal, scope=Scope(tenant_id="other", project_id="other")), e.ref)
    with pytest.raises(RepresentationError, match="profile_reference"):
        e.registry.read(e.principal, e.ref.model_dump())
    with pytest.raises(RepresentationError, match="profile_reference"):
        e.registry.read(e.principal, e.ref.model_copy(update={"version": True}))
    denied = replace(e.principal, actions=frozenset())
    for call in (
        lambda: e.registry.register(denied, e.profile),
        lambda: e.registry.read(denied, e.ref),
        lambda: e.leases.claim(denied, e.ref, e.source),
    ):
        with pytest.raises(UploadError, match="access_denied"):
            call()


def test_cache_commit_exact_replay_and_fresh_store_reconstruction(cache):
    e = cache
    lease = e.leases.claim(e.principal, e.ref, e.source)
    assert type(lease) is WorkLease and lease.fence == 1
    assert e.results.read(e.principal, lease.work) is None
    assert type(e.leases.claim(e.principal, e.ref, e.source)) is WorkBusy
    renewed = e.leases.renew(e.principal, lease)
    assert renewed.token == lease.token and renewed.expires_at >= lease.expires_at
    assert e.results.complete(e.principal, renewed, e.result) == e.result
    expire(e, renewed)
    assert EncodingResults(e.engine).complete(e.principal, renewed, e.result) == e.result
    assert EncodingResults(e.engine).read(e.principal, lease.work) == e.result
    hit = WorkLeases(e.engine).claim(replace(e.principal, actor_id="other"), e.ref, e.source)
    assert type(hit) is CacheHit and hit.result == e.result and hit.work == lease.work
    assert e.leases.release(e.principal, renewed) is False
    with pytest.raises(RepresentationError, match="work_complete"):
        e.leases.renew(e.principal, renewed)
    different = replace(e.result, vector=Float32Vector.from_values(e.profile.space, (1,) * 16))
    with pytest.raises(RepresentationError, match="result_conflict"):
        e.results.complete(e.principal, renewed, different)
    with pytest.raises(RepresentationError, match="stale_claim"):
        e.results.complete(e.principal, replace(renewed, token="other"), e.result)


def test_expiry_reclaim_fences_every_stale_mutation(cache):
    e = cache
    first = e.leases.claim(e.principal, e.ref, e.source)
    expire(e, first)
    with pytest.raises(RepresentationError, match="stale_claim"):
        e.results.complete(e.principal, first, e.result)
    with pytest.raises(RepresentationError, match="stale_claim"):
        e.leases.renew(e.principal, first)
    assert e.leases.release(e.principal, first) is False
    second = e.leases.claim(e.principal, e.ref, e.source)
    assert second.fence == 2 and second.token != first.token
    assert e.leases.release(e.principal, first) is False
    with pytest.raises(RepresentationError, match="stale_claim"):
        e.results.complete(e.principal, first, e.result)
    assert e.results.complete(e.principal, second, e.result) == e.result
    with pytest.raises(RepresentationError, match="stale_claim"):
        e.results.complete(e.principal, first, e.result)


def test_database_clock_expiry_and_explicit_release(cache):
    e = cache
    leases = WorkLeases(e.engine, LeasePolicy(1))
    first = leases.claim(e.principal, e.ref, e.source)
    with e.engine.begin() as connection:
        connection.execute(text("SELECT pg_sleep(1.05)"))
    with pytest.raises(RepresentationError, match="stale_claim"):
        leases.renew(e.principal, first)
    second = e.leases.claim(e.principal, e.ref, e.source)
    assert second.fence == first.fence + 1
    assert e.leases.release(e.principal, second)
    assert e.leases.claim(e.principal, e.ref, e.source).fence == second.fence + 1


def test_concurrent_connections_get_one_lease_and_persist_one_intent(cache):
    e = cache
    barrier = Barrier(4)

    def claim(index):
        barrier.wait(timeout=5)
        return WorkLeases(e.engine).claim(replace(e.principal, actor_id=f"worker-{index}"), e.ref, e.source)

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(claim, range(4)))
    winners = [x for x in outcomes if type(x) is WorkLease]
    assert len(winners) == 1 and sum(type(x) is WorkBusy for x in outcomes) == 3
    winner = winners[0]
    assert e.results.complete(replace(e.principal, actor_id=winner.actor_id), winner, e.result) == e.result
    with e.engine.begin() as connection:
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM artifacts.encoding_work WHERE "
                    "tenant_id=:tenant AND project_id=:project"
                ),
                e.principal.bindings,
            ).scalar_one()
            == 1
        )


def test_work_scope_profile_input_and_actor_cannot_be_swapped(cache):
    e = cache
    first = e.leases.claim(e.principal, e.ref, e.source)
    other_source = EncodingInput(b"different")
    assert e.leases.claim(e.principal, e.ref, other_source).work != first.work
    other_profile = replace(e.profile, version="2", space=replace(e.profile.space, normalization="l2"))
    ref = e.registry.register(e.principal, other_profile)
    assert e.leases.claim(e.principal, ref, e.source).work != first.work
    other_actor = replace(e.principal, actor_id="other")
    for call in (
        lambda: e.results.complete(other_actor, first, e.result),
        lambda: e.leases.renew(other_actor, first),
        lambda: e.leases.release(other_actor, first),
    ):
        with pytest.raises(RepresentationError, match="claim_actor"):
            call()
    with pytest.raises(RepresentationError, match="work_conflict"):
        e.results.complete(e.principal, first, replace(e.result, input_sha256=other_source.sha256))
    other_scope = replace(e.principal, scope=Scope(tenant_id="other", project_id=uuid.uuid4().hex))
    other_ref = e.registry.register(other_scope, e.profile)
    assert e.leases.claim(other_scope, other_ref, e.source).work != first.work
    with pytest.raises(RepresentationError, match="scope"):
        e.results.read(other_scope, first.work)
    missing = EncodingWorkIdentity.prepare(e.principal.scope, e.profile, EncodingInput(b"missing"))
    with pytest.raises(RepresentationError, match="work_missing"):
        e.results.read(e.principal, missing)


def test_service_role_cannot_rewrite_or_delete_history_or_lease_identity(cache):
    e = cache
    lease = e.leases.claim(e.principal, e.ref, e.source)
    e.results.complete(e.principal, lease, e.result)
    statements = [
        f"{verb} artifacts.{table}" + (" SET actor_id='changed'" if verb == "UPDATE" else "")
        for table in ("encoding_profiles", "encoding_work", "encoding_results")
        for verb in ("UPDATE", "DELETE FROM")
    ]
    statements += [
        "DELETE FROM artifacts.encoding_leases",
        "UPDATE artifacts.encoding_leases SET work_sha256='changed'",
    ]
    for statement in statements:
        with e.engine.connect() as connection:
            try:
                with pytest.raises(DBAPIError) as denied:
                    connection.execute(
                        text(statement + " WHERE tenant_id=:tenant AND project_id=:project"),
                        e.principal.bindings,
                    )
                assert denied.value.orig.sqlstate == "42501"
            finally:
                connection.rollback()
    assert e.results.read(e.principal, lease.work) == e.result


def test_claim_value_bounds_and_scope_are_explicit(cache):
    e = cache
    lease = e.leases.claim(e.principal, e.ref, e.source)
    for seconds in (0, 301, True):
        with pytest.raises(RepresentationError, match="lease_bound"):
            LeasePolicy(seconds)
    with pytest.raises(RepresentationError, match="lease_policy"):
        WorkLeases(e.engine, 30)
    for fields, reason in (
        ({"fence": True}, "fence_bound"),
        ({"fence": 0}, "fence_bound"),
        ({"expires_at": datetime(2026, 1, 1)}, "lease_time"),
        ({"work": None}, "work_required"),
    ):
        with pytest.raises(RepresentationError, match=reason):
            replace(lease, **fields)
    with pytest.raises(RepresentationError, match="encoded_required"):
        e.results.complete(e.principal, lease, None)
    for call in (
        lambda: e.leases.renew(e.principal, None),
        lambda: e.leases.release(e.principal, None),
        lambda: e.results.complete(e.principal, None, e.result),
    ):
        with pytest.raises(RepresentationError, match="claim_required"):
            call()


def test_repeated_migration_preserves_existing_artifact_and_source_history(cache, artifact_database):
    e = cache

    def snapshot():
        with e.engine.connect() as connection:
            return {
                table: tuple(
                    connection.execute(
                        text(
                            "SELECT count(*),md5(coalesce(string_agg(md5(to_jsonb(t)::text),'' "
                            "ORDER BY md5(to_jsonb(t)::text)),'')) FROM artifacts." + table + " t"
                        )
                    ).one()
                )
                for table in ("catalog", "source_revisions", "derivations")
            }

    before = snapshot()
    url = artifact_database.set(username="artifact_migrator")
    upgrade(url.render_as_string(hide_password=False))
    upgrade(url.render_as_string(hide_password=False))
    assert snapshot() == before
    migrator = create_engine(url)
    try:
        with migrator.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM artifacts.alembic_version")).scalar_one()
                == "artifact_0013"
            )
    finally:
        migrator.dispose()
    assert e.registry.read(e.principal, e.ref) == e.profile


def test_work_foreign_key_requires_exact_scoped_profile_and_exhaustion_is_explicit(cache):
    e = cache
    lease = e.leases.claim(e.principal, e.ref, e.source)
    statement = text(
        "INSERT INTO artifacts.encoding_work "
        "(tenant_id,project_id,work_sha256,profile_id,version,profile_sha256,input_sha256,actor_id) "
        "VALUES (:tenant,:project,:work,:profile,:version,:digest,:input,:actor)"
    )
    valid = e.principal.bindings | {
        "work": "a" * 64,
        "profile": e.ref.profile_id,
        "version": e.ref.version,
        "digest": e.ref.sha256,
        "input": e.source.sha256,
    }
    for changed in ({"project": uuid.uuid4().hex}, {"digest": "b" * 64}):
        with e.engine.connect() as connection:
            try:
                with pytest.raises(DBAPIError) as denied:
                    connection.execute(statement, valid | changed)
                assert denied.value.orig.sqlstate == "23503"
            finally:
                connection.rollback()
    with e.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE artifacts.encoding_leases SET fence=9007199254740991,"
                "expires_at=clock_timestamp()-interval '1 second' WHERE tenant_id=:tenant AND project_id=:project "
                "AND work_sha256=:work"
            ),
            e.principal.bindings | {"work": lease.work.sha256},
        )
    with pytest.raises(RepresentationError, match="fence_exhausted"):
        e.leases.claim(e.principal, e.ref, e.source)
