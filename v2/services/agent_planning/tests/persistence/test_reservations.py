import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.settlement import SettlementJournal
from amphora_agent_planning.providers import FixtureProvider, observe
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def policy(snapshot, units=60):
    context = snapshot.document().context.model_dump(mode="json")
    raw = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    raw.update(format="planning-budget-policy.v1", per_attempt_accounting_units=units)
    return BudgetPolicy.from_bytes(json.dumps(raw).encode())


def test_atomic_intent_reservation_replay_and_readback(stored):
    s = stored
    ledger = BudgetLedger(s.engine)
    reviewed = policy(s.snapshot)
    assert ledger.read(s.principal, s.first.reference()) is None
    with pytest.raises(ValueError, match="request_unknown"):
        ledger.reserve(s.principal, s.first, reviewed)
    s.journal.register(s.principal, s.snapshot)
    assert ledger.read(s.principal, s.first.reference()) is None
    reserved = ledger.reserve(s.principal, s.first, reviewed)
    assert reserved.demand.tokens == 2048 and reserved.demand.accounting_units == 60
    assert reserved.registered_at.tzinfo is not None
    assert s.journal.read_attempt(s.principal, s.first.reference()).observation is None
    assert ledger.reserve(s.principal, s.first, reviewed) == reserved
    replacement = create_engine(s.engine.url)
    try:
        assert BudgetLedger(replacement).read(s.principal, s.first.reference()) == reserved
    finally:
        replacement.dispose()


def test_pending_intent_and_conservative_hold_prevent_further_reservation(stored):
    s = stored
    s.journal.register(s.principal, s.snapshot)
    ledger, reviewed = BudgetLedger(s.engine), policy(s.snapshot)
    first = ledger.reserve(s.principal, s.first, reviewed)
    with pytest.raises(ValueError, match="attempt_pending"):
        ledger.reserve(s.principal, s.second, reviewed)
    s.journal.record(s.principal, s.first, observe(s.first, FixtureProvider("abstain")))
    # Even after settlement, v1 retains its 60-unit reservation floor.
    SettlementJournal(s.engine).settle(s.principal, s.first)
    with pytest.raises(ValueError, match="accounting_budget_exhausted"):
        ledger.reserve(s.principal, s.second, reviewed)
    assert ledger.read(s.principal, s.second.reference()) is None
    assert s.journal.read_attempt(s.principal, s.second.reference()) is None
    assert ledger.read(s.principal, s.first.reference()) == first


def test_exact_token_hold_is_independent_of_accounting_headroom(stored):
    s = stored
    raw = s.snapshot.document().model_dump(mode="json")
    raw["context"]["limits"]["total_tokens"] = 2048
    snapshot = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id=s.principal.actor_id, scope=s.principal.scope)
    first, second = AttemptBinding(snapshot, 1), AttemptBinding(snapshot, 2)
    reviewed, ledger = policy(snapshot, units=1), BudgetLedger(s.engine)
    s.journal.register(s.principal, snapshot)
    ledger.reserve(s.principal, first, reviewed)
    s.journal.record(s.principal, first, observe(first, FixtureProvider("interrupted")))
    SettlementJournal(s.engine).settle(s.principal, first)
    with pytest.raises(ValueError, match="token_budget_exhausted"):
        ledger.reserve(s.principal, second, reviewed)
    assert ledger.read(s.principal, second.reference()) is None


def test_changed_policy_or_request_does_not_reinterpret_reservation(stored):
    s = stored
    s.journal.register(s.principal, s.snapshot)
    ledger = BudgetLedger(s.engine)
    original = ledger.reserve(s.principal, s.first, policy(s.snapshot))
    with pytest.raises(ValueError, match="budget_policy_conflict"):
        ledger.reserve(s.principal, s.first, policy(s.snapshot, units=1))
    changed = RequestSnapshot.bind(s.snapshot.document().model_copy(update={"decision_scope": "f" * 64}),
                                    actor_id=s.principal.actor_id, scope=s.principal.scope)
    binding = AttemptBinding(changed, 1)
    with pytest.raises(ValueError, match="request_conflict"):
        ledger.reserve(s.principal, binding, policy(changed))
    with pytest.raises(ValueError, match="request_conflict"):
        ledger.read(s.principal, binding.reference())
    assert ledger.read(s.principal, s.first.reference()) == original


def test_unbudgeted_history_cannot_be_retroactively_authorized(stored):
    s = stored
    s.journal.register(s.principal, s.snapshot)
    s.journal.begin_attempt(s.principal, s.first)
    ledger = BudgetLedger(s.engine)
    with pytest.raises(ValueError, match="unbudgeted_attempt_history"):
        ledger.reserve(s.principal, s.first, policy(s.snapshot))
    assert ledger.read(s.principal, s.first.reference()) is None
    assert s.journal.read_attempt(s.principal, s.first.reference()).observation is None


def test_invalid_sequence_rolls_back_policy_and_intent_together(stored):
    s = stored
    s.journal.register(s.principal, s.snapshot)
    ledger = BudgetLedger(s.engine)
    with pytest.raises(ValueError, match="attempt_sequence"):
        ledger.reserve(s.principal, s.second, policy(s.snapshot))
    # Different policy can now be selected: the failed transaction retained no earlier policy row.
    actual = ledger.reserve(s.principal, s.first, policy(s.snapshot, units=10))
    assert actual.demand.accounting_units == 10


def test_concurrent_exact_reservation_has_one_hold_and_one_intent(stored):
    s = stored
    s.journal.register(s.principal, s.snapshot)
    ledger, reviewed, barrier = BudgetLedger(s.engine), policy(s.snapshot, units=40), Barrier(2)
    def reserve():
        barrier.wait(5)
        return ledger.reserve(s.principal, s.first, reviewed)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, replay = [future.result(10) for future in [pool.submit(reserve), pool.submit(reserve)]]
    assert first == replay
    s.journal.record(s.principal, s.first, observe(s.first, FixtureProvider("abstain")))
    SettlementJournal(s.engine).settle(s.principal, s.first)
    assert ledger.reserve(s.principal, s.second, reviewed).demand.accounting_units == 40
    with s.engine.connect() as connection:
        totals = connection.execute(text("SELECT count(*),sum(accounting_units) FROM planning.reservations "
            "WHERE tenant_id=:tenant AND project_id=:project"),
            {"tenant": s.principal.scope.tenant_id, "project": s.principal.scope.project_id}).one()
    assert tuple(totals) == (2, 80)


def test_permissions_and_database_immutability(stored):
    s = stored
    ledger = BudgetLedger(s.engine)
    denied = replace(s.principal, actions=frozenset())
    with pytest.raises(PermissionError):
        ledger.reserve(denied, s.first, policy(s.snapshot))
    with pytest.raises(PermissionError):
        ledger.read(denied, s.first.reference())
    for table in ("budget_policies", "reservations"):
        for command in (f"DELETE FROM planning.{table} WHERE false",
                        f"UPDATE planning.{table} SET tenant_id=tenant_id WHERE false"):
            with pytest.raises(DBAPIError) as failure, s.engine.begin() as connection:
                connection.execute(text(command))
            assert failure.value.orig.sqlstate == "42501"
