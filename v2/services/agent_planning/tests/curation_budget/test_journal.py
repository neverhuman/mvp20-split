"""Actual SQL scope caps, competing requests and no-refund replay; no paid calls."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.dispatch import DispatchJournal
from amphora_agent_planning.providers.capture import CapturedOutput, Observation, unknown_usage
from amphora_contracts_planning import ProviderUsage
from sqlalchemy import text

from ..curation_openai.test_adapter import source


def entry(stored, name, units=250000000):
    value = source().request.document().model_dump(mode='json')
    def rescope(row):
        if isinstance(row, dict):
            if set(row) == {'tenant_id', 'project_id'}: row.update(stored.principal.scope.model_dump())
            for child in row.values(): rescope(child)
        elif isinstance(row, list):
            for child in row: rescope(child)
    rescope(value)
    value['reference']['engagement_id'] = name
    value['actor_id'] = stored.principal.actor_id
    snapshot = RequestSnapshot.from_bytes(json.dumps(value).encode(), actor_id=stored.principal.actor_id,
                                         scope=stored.principal.scope)
    stored.journal.register(stored.principal, snapshot)
    context = value['context']
    policy = {key: context[key] for key in ('model', 'prompt', 'policy', 'output_schema', 'allowed_actions', 'limits')}
    policy.update(format='planning-budget-policy.v1', per_attempt_accounting_units=units)
    return AttemptBinding(snapshot, 1), BudgetPolicy.from_bytes(json.dumps(policy).encode())


def test_concurrent_fourth_slot_and_restart_cannot_reset_allowance(stored):
    ledger = BudgetLedger(stored.engine)
    for i in range(3): ledger.reserve(stored.principal, *entry(stored, 'first-' + str(i)))
    entries = [entry(stored, 'contender-' + str(i)) for i in range(2)]
    barrier = Barrier(2)
    def reserve(pair):
        barrier.wait(timeout=5)
        try:
            return BudgetLedger(stored.engine).reserve(stored.principal, *pair)
        except ValueError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, entries))
    assert sum(isinstance(result, str) for result in results) == 1
    assert 'curation_group_calls_exhausted' in results
    winner = next(pair for pair, result in zip(entries, results, strict=True) if not isinstance(result, str))
    assert BudgetLedger(stored.engine).reserve(stored.principal, *winner) in results
    with pytest.raises(ValueError, match='curation_group_calls_exhausted'):
        ledger.reserve(stored.principal, *entry(stored, 'fifth'))
    with stored.engine.connect() as conn:
        assert conn.execute(text('SELECT sum(accounting_units) FROM planning.reservations '
            'WHERE tenant_id=:tenant AND project_id=:project'),
            {'tenant': stored.principal.scope.tenant_id, 'project': stored.principal.scope.project_id}).scalar_one() == 1000000000


@pytest.mark.parametrize('units', [1, 250000001])
def test_invalid_reservation_never_creates_attempt(stored, units):
    binding, _valid_policy = entry(stored, 'bad')
    # The existing generic policy rejects a reservation above its total even
    # before the curation-specific ceiling. Both paths must leave no attempt.
    with pytest.raises(ValueError, match='curation_cost_reservation|budget_policy_accounting'):
        binding, policy = entry(stored, 'bad', units)
        BudgetLedger(stored.engine).reserve(stored.principal, binding, policy)
    assert stored.journal.read_attempt(stored.principal, binding.reference()) is None


@pytest.mark.parametrize('late', [False, True])
def test_primary_and_late_overage_block_new_issuance_before_settlement(stored, late):
    ledger, dispatch = BudgetLedger(stored.engine), DispatchJournal(stored.engine)
    first, policy = entry(stored, 'first')
    second, other_policy = entry(stored, 'second')
    ledger.reserve(stored.principal, first, policy)
    ledger.reserve(stored.principal, second, other_policy)
    ticket = dispatch.issue(stored.principal, first, 1 if late else 30)
    if late:
        time.sleep(1.05)
        dispatch.recover(stored.principal, first)
    observed = Observation.record(first, CapturedOutput(b'', False), 'unknown', 'adapter_failure',
        ProviderUsage(input_tokens=10, output_tokens=10, accounting_units=250000001, certainty='reported'))
    dispatch.complete(stored.principal, first, ticket, observed)
    with pytest.raises(ValueError, match='provider_usage_overage'): dispatch.issue(stored.principal, second, 30)
    with pytest.raises(ValueError, match='provider_usage_overage'):
        ledger.reserve(stored.principal, *entry(stored, 'fresh'))
    assert dispatch.issue(stored.principal, first, 30) is None


def test_unknown_outcome_does_not_refund_or_allow_a_second_issue(stored):
    ledger, dispatch = BudgetLedger(stored.engine), DispatchJournal(stored.engine)
    first, policy = entry(stored, 'unknown')
    reservation = ledger.reserve(stored.principal, first, policy)
    ticket = dispatch.issue(stored.principal, first, 30)
    dispatch.complete(stored.principal, first, ticket,
        Observation.record(first, CapturedOutput(b'', False), 'unknown', 'transport_lost', unknown_usage()))
    for i in range(3): ledger.reserve(stored.principal, *entry(stored, 'next-' + str(i)))
    assert ledger.read(stored.principal, first.reference()) == reservation
    assert DispatchJournal(stored.engine).issue(stored.principal, first, 30) is None
    with pytest.raises(ValueError, match='curation_group_calls_exhausted'):
        BudgetLedger(stored.engine).reserve(stored.principal, *entry(stored, 'no-refund'))
