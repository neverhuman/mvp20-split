"""Both journals, real claim contention, stale acknowledgement and bounded exhaustion."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_campaign_runtime.delivery.model import DeliveryPolicy
from amphora_campaign_runtime.delivery.store import DeliveryStore
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_core import Scope
from sqlalchemy import text


def expire(d, claim):
    assert claim.journal in {"outbox", "policy_outbox"}
    with d.env.engine.begin() as conn:
        conn.execute(text(f"UPDATE runtime.{claim.journal} SET lease_expires_at=clock_timestamp()-interval '1 second' "
                          "WHERE operation_id=:operation"), {"operation": claim.operation_id})


def test_both_journals_claim_and_ack_only_in_authorized_scope(delivery_env):
    d = delivery_env
    store = DeliveryStore(d.env.engine)
    with pytest.raises(TransitionError, match="access_denied"):
        store.claim(d.env.principal)
    other = replace(d.principal, scope=Scope(tenant_id=d.principal.scope.tenant_id, project_id="unowned"))
    assert store.claim(other) == ()
    claims = store.claim(d.principal)
    assert {c.journal for c in claims} == {"outbox", "policy_outbox"}
    for claim in claims:
        assert claim.notification().scope == d.principal.scope
        assert store.finish(d.principal, claim, acknowledged=True)
        assert store.finish(d.principal, claim, acknowledged=True) is False
    assert store.claim(d.principal) == ()


def test_two_contenders_cannot_lease_same_delivery(delivery_env):
    d = delivery_env
    store = DeliveryStore(d.env.engine)
    barrier = Barrier(2)
    def claim():
        barrier.wait(timeout=5)
        return store.claim(d.principal, limit=1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.submit(claim), pool.submit(claim)
        claims = (*first.result(timeout=10), *second.result(timeout=10))
    # One transaction may briefly lock both journal candidates; skipped work remains retryable.
    claims += store.claim(d.principal)
    assert len(claims) == 2 and len({c.operation_id for c in claims}) == 2


def test_reclaimed_delivery_fences_old_ack_and_failure(delivery_env):
    d = delivery_env
    store = DeliveryStore(d.env.engine)
    first, other = store.claim(d.principal)
    assert store.finish(d.principal, other, acknowledged=True)
    expire(d, first)
    assert store.finish(d.principal, first, acknowledged=True) is False
    successor = store.claim(d.principal)[0]
    assert successor.operation_id == first.operation_id
    assert successor.generation == first.generation + 1 and successor.token != first.token
    assert store.finish(d.principal, first, acknowledged=False) is False
    assert store.finish(d.principal, successor, acknowledged=True)


def test_failure_backoff_and_exhaustion_preserve_operational_state(delivery_env):
    d = delivery_env
    store = DeliveryStore(d.env.engine, DeliveryPolicy(max_attempts=2))
    first, other = store.claim(d.principal)
    store.finish(d.principal, other, acknowledged=True)
    assert store.finish(d.principal, first, acknowledged=False)
    assert store.claim(d.principal) == ()
    with d.env.engine.begin() as conn:
        conn.execute(text(f"UPDATE runtime.{first.journal} SET available_at=clock_timestamp()-interval '1 second' "
                          "WHERE operation_id=:operation"), {"operation": first.operation_id})
    retry = store.claim(d.principal)[0]
    store.finish(d.principal, retry, acknowledged=False)
    with d.env.engine.connect() as conn:
        row = conn.execute(text(f"SELECT status,delivery_attempts,last_reason FROM runtime.{retry.journal} "
                                "WHERE operation_id=:operation"), {"operation": retry.operation_id}).one()
    assert tuple(row) == ("exhausted", 2, "delivery_failed")
    assert store.claim(d.principal) == ()


def test_worker_death_on_last_attempt_exhausts_after_lease(delivery_env):
    d = delivery_env
    store = DeliveryStore(d.env.engine, DeliveryPolicy(max_attempts=1))
    claims = store.claim(d.principal)
    for claim in claims:
        expire(d, claim)
    assert store.claim(d.principal) == ()
    with d.env.engine.connect() as conn:
        for claim in claims:
            assert conn.execute(text(f"SELECT status FROM runtime.{claim.journal} WHERE operation_id=:operation"),
                                {"operation": claim.operation_id}).scalar_one() == "exhausted"
