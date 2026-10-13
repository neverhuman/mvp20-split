"""Owner-reviewed exact-scope extension; original holds and concurrency remain authoritative."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from amphora_agent_planning.curation_budget import ceiling
from amphora_agent_planning.curation_budget.journal import check
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.dispatch import DispatchJournal
from .test_journal import entry


def test_extension_requires_exact_tenant_and_project():
    tenant, project = ceiling.REVIEWED_EXTENSION
    approved = ceiling.ceiling_for({'tenant': tenant, 'project': project})
    assert (approved.maximum_calls, approved.maximum_units, approved.authorization) == (53, 13300000000, 'UI-01.08i')
    for key in ({'tenant': 'other', 'project': project}, {'tenant': tenant, 'project': 'other'}):
        default = ceiling.ceiling_for(key)
        assert (default.maximum_calls, default.maximum_units) == (4, 1000000000)


def test_original_four_holds_survive_extension_and_fifty_third_slot_race(stored, monkeypatch):
    ledger = BudgetLedger(stored.engine)
    originals = [entry(stored, 'original-' + str(i)) for i in range(4)]
    retained = [ledger.reserve(stored.principal, *pair) for pair in originals]
    fifth = entry(stored, 'fifth', version='2')
    with pytest.raises(ValueError, match='curation_group_calls_exhausted'):
        ledger.reserve(stored.principal, *fifth)
    scope = stored.principal.scope
    monkeypatch.setattr(ceiling, 'REVIEWED_EXTENSION', (scope.tenant_id, scope.project_id))
    ledger.reserve(stored.principal, *fifth)
    sixth = entry(stored, 'sixth', version='2')
    ledger.reserve(stored.principal, *sixth)
    for name in ('seventh', 'eighth', 'ninth'):
        ledger.reserve(stored.principal, *entry(stored, name, version='3'))
    ledger.reserve(stored.principal, *entry(stored, 'tenth', units=300000000, version='5'))
    ledger.reserve(stored.principal, *entry(stored, 'eleventh', units=250000000, version='6'))
    ledger.reserve(stored.principal, *entry(stored, 'twelfth', units=250000000, version='7'))
    for index in range(13, 53):
        ledger.reserve(stored.principal, *entry(stored, 'retained-' + str(index), units=250000000, version='8'))
    pairs = [entry(stored, 'fifty-third-' + str(i), units=250000000, version='8') for i in range(2)]
    barrier = Barrier(2)
    def reserve(pair):
        barrier.wait(timeout=5)
        try:
            return BudgetLedger(stored.engine).reserve(stored.principal, *pair)
        except ValueError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, pairs))
    assert sum(result == 'curation_group_calls_exhausted' for result in results) == 1
    for pair, original in zip(originals, retained):
        assert BudgetLedger(stored.engine).reserve(stored.principal, *pair) == original
    with stored.engine.begin() as connection:
        check(connection, {'tenant': scope.tenant_id, 'project': scope.project_id})
    # Dispatch sees the same fifty-three-slot policy, rather than the predecessor four-slot cap.
    assert DispatchJournal(stored.engine).issue(stored.principal, fifth[0], 30) is not None
    assert DispatchJournal(stored.engine).issue(stored.principal, fifth[0], 30) is None
    with pytest.raises(ValueError, match='curation_group_calls_exhausted'):
        ledger.reserve(stored.principal, *entry(stored, 'fifty-fourth', units=250000000, version='8'))
