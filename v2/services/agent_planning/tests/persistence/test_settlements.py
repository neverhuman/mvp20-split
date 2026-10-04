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
from amphora_agent_planning.providers.capture import Observation
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def prepare(s, units=40):
    context = s.snapshot.document().context.model_dump(mode="json")
    raw = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    raw.update(format="planning-budget-policy.v1", per_attempt_accounting_units=units)
    policy = BudgetPolicy.from_bytes(json.dumps(raw).encode())
    ledger, settlements = BudgetLedger(s.engine), SettlementJournal(s.engine)
    s.journal.register(s.principal, s.snapshot)
    ledger.reserve(s.principal, s.first, policy)
    return ledger, settlements, policy


def test_pending_and_unsettled_are_distinct_and_retry_charges_both_attempts(stored):
    s = stored
    ledger, settlements, policy = prepare(s)
    assert settlements.read(s.principal, s.first.reference()) is None
    with pytest.raises(ValueError, match="attempt_pending"):
        settlements.settle(s.principal, s.first)
    observed = observe(s.first, FixtureProvider("interrupted"))
    s.journal.record(s.principal, s.first, observed)
    with pytest.raises(ValueError, match="attempt_unsettled"):
        ledger.reserve(s.principal, s.second, policy)
    first = settlements.settle(s.principal, s.first)
    assert first.charge.tokens == 2048 and first.charge.accounting_units == 40
    assert not first.charge.overage and first.registered_at.tzinfo is not None
    assert settlements.settle(s.principal, s.first) == first
    ledger.reserve(s.principal, s.second, policy)
    s.journal.record(s.principal, s.second, observe(s.second, FixtureProvider("abstain")))
    second = settlements.settle(s.principal, s.second)
    assert first.charge.tokens + second.charge.tokens == 4096
    assert first.charge.accounting_units + second.charge.accounting_units == 80
    assert s.journal.read_attempt(s.principal, s.first.reference()).observation == observed
    replacement = create_engine(s.engine.url)
    try:
        assert SettlementJournal(replacement).read(s.principal, s.first.reference()) == first
        assert SettlementJournal(replacement).read(s.principal, s.second.reference()) == second
    finally:
        replacement.dispose()


@pytest.mark.parametrize("field,value", [("input_tokens", 2000), ("output_tokens", 2000),
                                        ("accounting_units", 9007199254740991)])
def test_observed_overage_is_exact_and_stops_new_admission(stored, field, value):
    s = stored
    ledger, settlements, policy = prepare(s)
    observed = observe(s.first, FixtureProvider("interrupted"))
    wire = observed.document().model_dump(mode="json")
    wire["usage"][field] = value
    observed = Observation(observed.capture, json.dumps(wire).encode())
    s.journal.record(s.principal, s.first, observed)
    result = settlements.settle(s.principal, s.first)
    assert getattr(result.charge, field) == value and result.charge.overage
    with pytest.raises(ValueError, match="provider_usage_overage"):
        ledger.reserve(s.principal, s.second, policy)
    assert ledger.read(s.principal, s.second.reference()) is None
    # Historical reservation remains replayable; replay does not grant dispatch authority.
    assert ledger.reserve(s.principal, s.first, policy) == ledger.read(s.principal, s.first.reference())


def test_exact_concurrent_settlement_has_one_immutable_record(stored):
    s = stored
    _, settlements, _ = prepare(s)
    s.journal.record(s.principal, s.first, observe(s.first, FixtureProvider("malformed")))
    barrier = Barrier(2)
    def settle():
        barrier.wait(5)
        return settlements.settle(s.principal, s.first)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, replay = [f.result(10) for f in [pool.submit(settle), pool.submit(settle)]]
    assert first == replay and first.charge.accounting_units == 40
    for statement in ("UPDATE planning.settlements SET accounting_units=1", "DELETE FROM planning.settlements"):
        with pytest.raises(DBAPIError), s.engine.begin() as connection:
            connection.execute(text(statement))


def test_settlement_requires_exact_request_actor_grants_and_reservation(stored):
    s = stored
    settlements = SettlementJournal(s.engine)
    assert settlements.read(s.principal, s.first.reference()) is None
    with pytest.raises(ValueError, match="request_unknown"):
        settlements.settle(s.principal, s.first)
    s.journal.register(s.principal, s.snapshot)
    with pytest.raises(ValueError, match="reservation_unknown"):
        settlements.settle(s.principal, s.first)
    changed = RequestSnapshot.bind(s.snapshot.document().model_copy(update={"decision_scope": "f" * 64}),
                                   actor_id=s.principal.actor_id, scope=s.principal.scope)
    for method, argument in ((settlements.settle, AttemptBinding(changed, 1)),
                             (settlements.read, AttemptBinding(changed, 1).reference())):
        with pytest.raises(ValueError, match="request_conflict"):
            method(s.principal, argument)
    with pytest.raises(ValueError, match="request_actor_mismatch"):
        settlements.settle(replace(s.principal, actor_id="other"), s.first)
    with pytest.raises(PermissionError):
        settlements.settle(replace(s.principal, actions=frozenset()), s.first)
    with pytest.raises(PermissionError):
        settlements.read(replace(s.principal, actions=frozenset()), s.first.reference())
