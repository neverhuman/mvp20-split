"""A late answer cannot replace a failed measured primary or refund its allowance."""

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from amphora_agent_planning.providers import FixtureProvider
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_planning import ProviderUsage

from .test_runner import setup

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('late_units', [1, 101])
def test_expired_primary_survives_late_success_and_late_overage(stored, late_units):
    entered, released = Event(), Event()
    class Delayed:
        def supports(self, _model):
            return True
        def reply(self, attempt):
            entered.set()
            assert released.wait(15)
            result = FixtureProvider('abstain').reply(attempt)
            return ProviderReply(result.chunks, ProviderUsage(input_tokens=10, output_tokens=10,
                                                             accounting_units=late_units, certainty='reported'))
    protocol, batch, provider, runner = setup(stored, Delayed(), timeout=1)
    suite = protocol.manifest.suite_id
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(runner.step, stored.principal, suite)
        try:
            assert entered.wait(5)
            time.sleep(1.1)
            recovered = runner.step(stored.principal, suite)
            assert recovered.observations[0].observation.status == 'unknown'
            primary = recovered.observations[0]
            assert provider.calls == 1
        finally:
            released.set()
        future.result(10)
    late = runner.runner.dispatch.read_late(stored.principal, batch.tasks[0].binding)
    assert late.document().status == 'abstained'
    assert runner.read(stored.principal, suite).observations[0] == primary
    final = runner.step(stored.principal, suite)
    assert final.observations[0] == primary and not final.passed
    if late_units == 101:
        assert final.status == 'budget_overage' and provider.calls == 1
        assert runner.runner.journal.read_attempt(stored.principal, batch.tasks[1].binding.reference()) is None
    else:
        assert final.status == 'complete' and provider.calls == 2


def test_late_overage_recovers_an_already_issued_second_repetition_without_new_call(stored):
    entered = [Event(), Event()]
    released = [Event(), Event()]
    class Delayed:
        calls = 0
        def supports(self, _model):
            return True
        def reply(self, attempt):
            index = self.calls
            self.calls += 1
            entered[index].set()
            assert released[index].wait(20)
            result = FixtureProvider('abstain').reply(attempt)
            return ProviderReply(result.chunks, ProviderUsage(input_tokens=10, output_tokens=10,
                accounting_units=101 if index == 0 else 1, certainty='reported'))
    protocol, _, provider, runner = setup(stored, Delayed(), timeout=2)
    suite = protocol.manifest.suite_id
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(runner.step, stored.principal, suite)
        try:
            assert entered[0].wait(5)
            time.sleep(2.1)
            assert runner.step(stored.principal, suite).observations[0].observation.status == 'unknown'
            second = pool.submit(runner.step, stored.principal, suite)
            assert entered[1].wait(5)
            released[0].set()
            first.result(10)
            pending = runner.step(stored.principal, suite)
            assert pending.status == 'budget_overage' and len(pending.observations) == 1
            time.sleep(2.1)
            recovered = runner.step(stored.principal, suite)
            assert recovered.status == 'budget_overage'
            assert [item.observation.status for item in recovered.observations] == ['unknown', 'unknown']
            assert provider.calls == 2
        finally:
            for release in released:
                release.set()
        second.result(10)
    assert runner.read(stored.principal, suite) == recovered


def test_overage_does_not_issue_an_existing_reservation_without_ticket(stored):
    class Overage:
        def supports(self, _model):
            return True
        def reply(self, attempt):
            result = FixtureProvider('abstain').reply(attempt)
            return ProviderReply(result.chunks, ProviderUsage(input_tokens=10, output_tokens=10,
                                                             accounting_units=101, certainty='reported'))
    protocol, batch, provider, runner = setup(stored, Overage())
    task = batch.tasks[1]
    runner.runner.journal.register(stored.principal, task.request)
    runner.runner.ledger.reserve(stored.principal, task.binding, task.policy)
    runner.step(stored.principal, protocol.manifest.suite_id)
    result = runner.step(stored.principal, protocol.manifest.suite_id)
    assert result.status == 'budget_overage' and provider.calls == 1
    assert runner.runner.journal.read_attempt(stored.principal, task.binding.reference()).observation is None
