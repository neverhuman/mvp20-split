import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.dispatch import DispatchJournal
from amphora_agent_planning.persistence.settlement import SettlementJournal
from amphora_agent_planning.providers import FixtureProvider, observe
from amphora_agent_planning.providers.capture import Observation
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def prepare(s):
    context = s.snapshot.document().context.model_dump(mode="json")
    raw = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    raw.update(format="planning-budget-policy.v1", per_attempt_accounting_units=40)
    policy = BudgetPolicy.from_bytes(json.dumps(raw).encode())
    ledger = BudgetLedger(s.engine)
    s.journal.register(s.principal, s.snapshot)
    ledger.reserve(s.principal, s.first, policy)
    return DispatchJournal(s.engine), ledger, SettlementJournal(s.engine), policy


def expire(s, ticket):
    # Actual database clock, no fixture timestamp mutation or arbitrary long sleep.
    with s.engine.connect() as connection:
        remaining = connection.execute(text("SELECT EXTRACT(EPOCH FROM (:deadline-clock_timestamp()))"),
                                       {"deadline": ticket.deadline}).scalar_one()
    time.sleep(max(0, float(remaining)) + 0.03)


def test_concurrent_issuance_grants_exactly_one_worker_then_timely_completion(stored):
    s = stored
    dispatch, _, _, _ = prepare(s)
    barrier = Barrier(2)
    def issue():
        barrier.wait(5)
        return dispatch.issue(s.principal, s.first, 10)
    with ThreadPoolExecutor(max_workers=2) as pool:
        tickets = [f.result(10) for f in [pool.submit(issue), pool.submit(issue)]]
    assert sum(ticket is not None for ticket in tickets) == 1
    ticket = next(t for t in tickets if t is not None)
    assert ticket.deadline.tzinfo is not None
    with pytest.raises(ValueError, match="attempt_not_expired"):
        dispatch.recover(s.principal, s.first)
    result = observe(s.first, FixtureProvider("abstain"))
    with pytest.raises(ValueError, match="dispatch_ticket_mismatch"):
        dispatch.complete(s.principal, s.first, replace(ticket, token="wrong"), result)
    recorded = dispatch.complete(s.principal, s.first, ticket, result)
    assert recorded.observation == result
    assert dispatch.complete(s.principal, s.first, ticket, result) == recorded
    assert dispatch.recover(s.principal, s.first) == recorded
    assert dispatch.issue(s.principal, s.first, 10) is None
    assert dispatch.read_late(s.principal, s.first) is None
    with pytest.raises(ValueError, match="observation_conflict"):
        dispatch.complete(s.principal, s.first, ticket, observe(s.first, FixtureProvider("proposal")))


def test_expiry_keeps_late_response_separate_and_does_not_duplicate_charge(stored):
    s = stored
    dispatch, ledger, settlements, policy = prepare(s)
    ticket = dispatch.issue(s.principal, s.first, 1)
    expire(s, ticket)
    recovered = dispatch.recover(s.principal, s.first)
    assert recovered.observation.document().status == "unknown"
    assert recovered.observation.document().reason_code == "attempt_deadline"
    settled = settlements.settle(s.principal, s.first)
    result = observe(s.first, FixtureProvider("proposal"))
    assert dispatch.complete(s.principal, s.first, ticket, result) == recovered
    assert dispatch.complete(s.principal, s.first, ticket, result) == recovered
    assert dispatch.read_late(s.principal, s.first) == result
    assert settlements.read(s.principal, s.first.reference()) == settled
    # One 40-unit charge, not 40+40 for the same physical attempt.
    ledger.reserve(s.principal, s.second, policy)
    assert dispatch.issue(s.principal, s.second, 10) is not None
    with pytest.raises(ValueError, match="late_observation_conflict"):
        dispatch.complete(s.principal, s.first, ticket, observe(s.first, FixtureProvider("abstain")))


@pytest.mark.parametrize("reserve_second_before_late", [False, True])
def test_late_overage_blocks_new_reservation_or_unissued_reserved_call(stored, reserve_second_before_late):
    s = stored
    dispatch, ledger, settlements, policy = prepare(s)
    ticket = dispatch.issue(s.principal, s.first, 1)
    expire(s, ticket)
    dispatch.recover(s.principal, s.first)
    settlements.settle(s.principal, s.first)
    if reserve_second_before_late:
        ledger.reserve(s.principal, s.second, policy)
    late = observe(s.first, FixtureProvider("interrupted"))
    wire = late.document().model_dump(mode="json")
    wire["usage"]["accounting_units"] = 9007199254740991
    late = Observation(late.capture, json.dumps(wire).encode())
    dispatch.complete(s.principal, s.first, ticket, late)
    assert dispatch.read_late(s.principal, s.first).document().usage.accounting_units == 9007199254740991
    with pytest.raises(ValueError, match="provider_usage_overage"):
        if reserve_second_before_late:
            dispatch.issue(s.principal, s.second, 10)
        else:
            ledger.reserve(s.principal, s.second, policy)


def test_completion_after_deadline_itself_records_recovery_and_late_output(stored):
    s = stored
    dispatch, _, _, _ = prepare(s)
    ticket = dispatch.issue(s.principal, s.first, 1)
    expire(s, ticket)
    actual = observe(s.first, FixtureProvider("abstain"))
    recorded = dispatch.complete(s.principal, s.first, ticket, actual)
    assert recorded.observation.document().reason_code == "attempt_deadline"
    assert dispatch.read_late(s.principal, s.first) == actual
    for table in ("dispatches", "late_observations"):
        with pytest.raises(DBAPIError), s.engine.begin() as connection:
            connection.execute(text("DELETE FROM planning." + table))


@pytest.mark.parametrize("timeout", [0, -1, True, 1.0, 86401])
def test_timeout_must_be_bounded_owner_integer(stored, timeout):
    with pytest.raises(ValueError, match="dispatch_timeout"):
        DispatchJournal(stored.engine).issue(stored.principal, stored.first, timeout)


def test_missing_request_reservation_issuance_and_grants(stored):
    s = stored
    dispatch = DispatchJournal(s.engine)
    with pytest.raises(ValueError, match="request_unknown"):
        dispatch.issue(s.principal, s.first, 10)
    s.journal.register(s.principal, s.snapshot)
    with pytest.raises(ValueError, match="reservation_unknown"):
        dispatch.issue(s.principal, s.first, 10)
    prepare(s)
    with pytest.raises(ValueError, match="dispatch_unknown"):
        dispatch.recover(s.principal, s.first)
    with pytest.raises(PermissionError):
        dispatch.issue(replace(s.principal, actions=frozenset()), s.first, 10)
    s.journal.record(s.principal, s.first, observe(s.first, FixtureProvider("abstain")))
    with pytest.raises(ValueError, match="attempt_already_observed"):
        dispatch.issue(s.principal, s.first, 10)
