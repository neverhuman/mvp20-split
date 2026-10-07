"""Real SQL scope ceiling, contention, replay and primary/late overage oracles."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.dispatch import DispatchJournal
from amphora_agent_planning.providers.capture import (
    CapturedOutput,
    Observation,
    unknown_usage,
)
from amphora_contracts_planning import ProviderUsage

from ..checkpoint_openai.test_adapter import source

pytestmark = pytest.mark.postgres


def entry(stored, name, *, units=58368000):
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


def test_scope_ceiling_survives_new_ledger_and_competing_reservations(stored):
    ledger = BudgetLedger(stored.engine)
    for i in range(5):
        binding, policy = entry(stored, 'first-' + str(i))
        ledger.reserve(stored.principal, binding, policy)
    entries = [entry(stored, 'contender-' + str(i)) for i in range(2)]
    barrier = Barrier(2)
    def reserve(pair):
        barrier.wait(5)
        try:
            return BudgetLedger(stored.engine).reserve(stored.principal, *pair)
        except ValueError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, entries))
    assert sum(isinstance(result, str) for result in results) == 1
    assert 'checkpoint_group_calls_exhausted' in results
    winner = next(pair for pair, result in zip(entries, results, strict=True) if not isinstance(result, str))
    # A fresh object has no resettable allowance; exact existing reservation still replays.
    assert BudgetLedger(stored.engine).reserve(stored.principal, *winner) in results
    with pytest.raises(ValueError, match='checkpoint_group_calls_exhausted'):
        BudgetLedger(stored.engine).reserve(stored.principal, *entry(stored, 'seventh'))


def test_money_ceiling_and_underreserved_template_precede_issuance(stored):
    ledger = BudgetLedger(stored.engine)
    for i in range(2):
        ledger.reserve(stored.principal, *entry(stored, 'cost-' + str(i), units=250000000))
    with pytest.raises(ValueError, match='checkpoint_group_cost_exhausted'):
        ledger.reserve(stored.principal, *entry(stored, 'excess'))
    binding, policy = entry(stored, 'under', units=1)
    with pytest.raises(ValueError, match='checkpoint_cost_underreserved'):
        ledger.reserve(stored.principal, binding, policy)
    assert stored.journal.read_attempt(stored.principal, binding.reference()) is None


@pytest.mark.parametrize('late', [False, True])
def test_known_primary_or_late_overage_blocks_other_reserved_and_fresh_work(stored, late):
    ledger, dispatch = BudgetLedger(stored.engine), DispatchJournal(stored.engine)
    first, policy = entry(stored, 'first')
    second, second_policy = entry(stored, 'second')
    ledger.reserve(stored.principal, first, policy)
    ledger.reserve(stored.principal, second, second_policy)
    ticket = dispatch.issue(stored.principal, first, 1 if late else 30)
    if late:
        time.sleep(1.05)
        dispatch.recover(stored.principal, first)
    usage = ProviderUsage(input_tokens=100, output_tokens=10, accounting_units=60000000, certainty='reported')
    observed = Observation.record(first, CapturedOutput(b'', False), 'unknown', 'adapter_failure', usage)
    dispatch.complete(stored.principal, first, ticket, observed)
    # Before settlement: the immutable observed report is already enough.
    with pytest.raises(ValueError, match='provider_usage_overage'):
        dispatch.issue(stored.principal, second, 30)
    with pytest.raises(ValueError, match='provider_usage_overage'):
        ledger.reserve(stored.principal, *entry(stored, 'fresh'))
    assert dispatch.issue(stored.principal, first, 30) is None


def test_unknown_failure_retains_original_allowance_without_refund(stored):
    ledger, dispatch = BudgetLedger(stored.engine), DispatchJournal(stored.engine)
    first, policy = entry(stored, 'unknown', units=500000000)
    original = ledger.reserve(stored.principal, first, policy)
    ticket = dispatch.issue(stored.principal, first, 30)
    dispatch.complete(stored.principal, first, ticket,
        Observation.record(first, CapturedOutput(b'', False), 'unknown', 'adapter_failure', unknown_usage()))
    assert ledger.read(stored.principal, first.reference()) == original
    with pytest.raises(ValueError, match='checkpoint_group_cost_exhausted'):
        BudgetLedger(stored.engine).reserve(stored.principal, *entry(stored, 'no-refund'))
