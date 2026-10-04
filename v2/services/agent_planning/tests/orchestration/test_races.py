"""Named barriers exercise runner behavior while an actual owner call is outstanding."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.providers import FixtureProvider
from sqlalchemy import text

pytestmark = pytest.mark.postgres


def policy(snapshot):
    context = snapshot.document().context.model_dump(mode="json")
    raw = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    raw.update(format="planning-budget-policy.v1", per_attempt_accounting_units=40)
    return BudgetPolicy.from_bytes(json.dumps(raw).encode())


def test_unrelated_engagement_progresses_while_same_attempt_competitors_remain_pending(stored):
    s = stored
    entered, released = Event(), Event()
    calls = []
    def barrier():
        calls.append(1)
        entered.set()
        assert released.wait(15)
    runner = PlanningRunner(s.engine, FixtureProvider("delayed", barrier), timeout_seconds=30)
    raw = s.snapshot.document().model_dump(mode="json")
    raw["reference"]["engagement_id"] = "independent-engagement"
    other = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id=s.principal.actor_id,
                                       scope=s.principal.scope)
    fast = PlanningRunner(s.engine, FixtureProvider("abstain"), timeout_seconds=30)
    with ThreadPoolExecutor(max_workers=5) as pool:
        pending = pool.submit(runner.run, s.principal, s.snapshot, policy(s.snapshot))
        try:
            assert entered.wait(5)
            contenders = [pool.submit(runner.run, s.principal, s.snapshot, policy(s.snapshot)) for _ in range(3)]
            independent = pool.submit(fast.run, s.principal, other, policy(other))
            assert independent.result(5).stop_reason == "abstained"
            assert all(f.result(5).stop_reason == "attempt_pending" for f in contenders)
            assert calls == [1] and not pending.done()
        finally:
            released.set()
        assert pending.result(5).stop_reason == "abstained"
    assert runner.run(s.principal, s.snapshot, policy(s.snapshot)).stop_reason == "abstained"
    assert calls == [1]


@pytest.mark.parametrize("ordering", ["recover-first", "return-first", "simultaneous"])
def test_expired_live_worker_cannot_overwrite_recovery_under_any_barrier_order(stored, ordering):
    s = stored
    entered, released = Event(), Event()
    def barrier():
        entered.set()
        assert released.wait(15)
    runner = PlanningRunner(s.engine, FixtureProvider("delayed", barrier), timeout_seconds=1)
    with ThreadPoolExecutor(max_workers=3) as pool:
        worker = pool.submit(runner.execute, s.principal, s.first, policy(s.snapshot))
        try:
            assert entered.wait(5)
            with s.engine.connect() as connection:
                remaining = connection.execute(text("SELECT EXTRACT(EPOCH FROM (deadline-clock_timestamp())) "
                    "FROM planning.dispatches WHERE tenant_id=:tenant AND project_id=:project"),
                    {"tenant": s.principal.scope.tenant_id, "project": s.principal.scope.project_id}).scalar_one()
            time.sleep(max(0, float(remaining)) + 0.03)
            if ordering == "recover-first":
                recovery = runner.dispatch.recover(s.principal, s.first)
                released.set()
                completed = worker.result(5)
            elif ordering == "return-first":
                released.set()
                completed = worker.result(5)
                recovery = runner.dispatch.recover(s.principal, s.first)
            else:
                start = Barrier(2)
                def recover():
                    start.wait(5)
                    return runner.dispatch.recover(s.principal, s.first)
                def release():
                    start.wait(5)
                    released.set()
                recovering = pool.submit(recover)
                pool.submit(release).result(5)
                recovery, completed = recovering.result(5), worker.result(5)
        finally:
            released.set()
    assert completed == recovery
    assert recovery.observation.document().reason_code == "attempt_deadline"
    late = runner.dispatch.read_late(s.principal, s.first)
    assert late.document().status == "abstained"
    assert runner.journal.read_attempt(s.principal, s.first.reference()) == recovery
    settlement = runner.settlements.read(s.principal, s.first.reference())
    assert settlement.charge.tokens == 2048 and settlement.charge.accounting_units == 40
