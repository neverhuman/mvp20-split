"""Actual Planning issuance, conservative accounting and complete repetition denominators."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Event

import pytest
from amphora_agent_planning.evaluation import EvaluationProtocol
from amphora_agent_planning.evaluation_batch import EvaluationBatch
from amphora_agent_planning.evaluation_batch.storage import EvaluationJournal
from amphora_agent_planning.evaluation_execution import EvaluationRunner
from amphora_agent_planning.providers import FixtureProvider
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_planning import ProviderUsage
from sqlalchemy import text

from ..evaluation_batch.test_binding import prepared

pytestmark = pytest.mark.postgres


class Counted:
    def __init__(self, provider):
        self.provider, self.calls = provider, 0

    def supports(self, model):
        return self.provider.supports(model)

    def reply(self, attempt):
        self.calls += 1
        return self.provider.reply(attempt)


def setup(stored, provider, *, repetitions=2, mode='fixture', timeout=30, assertions=None):
    protocol, _, requests, policies = prepared(snapshot=stored.snapshot, repetitions=repetitions)
    manifest = protocol.manifest.model_dump(mode='json')
    manifest['mode'] = mode
    corpus = protocol.corpus_bytes
    if assertions is not None:
        labels = json.loads(corpus)
        labels['cases'][0]['assertions'] = assertions
        labels['cases'][0]['hard_authority'] = True
        corpus = json.dumps(labels).encode()
        manifest['corpus_sha256'] = hashlib.sha256(corpus).hexdigest()
    protocol = EvaluationProtocol.load(json.dumps(manifest).encode(), corpus)
    batch = EvaluationBatch.prepare(protocol, stored.principal, requests, policies)
    EvaluationJournal(stored.engine).register(stored.principal, protocol, batch)
    counted = Counted(provider)
    runner = EvaluationRunner(stored.engine, counted, adapter_revision='fixture-1', timeout_seconds=timeout)
    return protocol, batch, counted, runner


@pytest.mark.parametrize('variant,status,passed', [('abstain', 'scientific_abstention', True),
    ('malformed', 'invalid', False), ('unavailable', 'provider_error', False), ('interrupted', 'unknown', False)])
def test_every_measured_repetition_is_retained_without_hidden_retry(stored, variant, status, passed):
    protocol, batch, provider, runner = setup(stored, FixtureProvider(variant))
    suite = protocol.manifest.suite_id
    initial = runner.read(stored.principal, suite)
    assert initial.status == 'pending' and initial.score.categories[0].present == 0
    first = runner.step(stored.principal, suite)
    assert first.status == 'pending' and len(first.observations) == provider.calls == 1
    final = runner.step(stored.principal, suite)
    assert final.status == 'complete' and final.passed == passed
    assert [item.observation.status for item in final.observations] == [status, status]
    assert provider.calls == 2
    replacement = EvaluationRunner(stored.engine, provider, adapter_revision='fixture-1', timeout_seconds=30)
    assert replacement.step(stored.principal, suite) == final and provider.calls == 2
    for task in batch.tasks:
        charge = runner.runner.settlements.read(stored.principal, task.binding.reference()).charge
        assert charge.accounting_units == task.demand.accounting_units


def test_concurrent_step_reads_pending_without_a_second_call(stored):
    entered, released = Event(), Event()
    def barrier():
        entered.set()
        assert released.wait(10)
    protocol, _, provider, runner = setup(stored, FixtureProvider('delayed', barrier))
    suite = protocol.manifest.suite_id
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(runner.step, stored.principal, suite)
        try:
            assert entered.wait(5)
            pending = runner.step(stored.principal, suite)
            assert pending.status == 'pending' and not pending.observations and provider.calls == 1
        finally:
            released.set()
        assert future.result(10).score.categories[0].present == 1
    assert runner.step(stored.principal, suite).passed and provider.calls == 2


def test_reported_overage_stops_unissued_repetitions_without_refund(stored):
    class Overage:
        def supports(self, _model):
            return True
        def reply(self, binding):
            result = FixtureProvider('abstain').reply(binding)
            return ProviderReply(result.chunks, ProviderUsage(input_tokens=10, output_tokens=10,
                                                             accounting_units=101, certainty='reported'))
    protocol, batch, provider, runner = setup(stored, Overage())
    suite = protocol.manifest.suite_id
    first = runner.step(stored.principal, suite)
    assert first.status == 'budget_overage' and not first.passed
    assert runner.step(stored.principal, suite) == first and provider.calls == 1
    assert runner.runner.journal.read_attempt(stored.principal, batch.tasks[1].binding.reference()) is None
    assert first.score.categories[0].planned == 2 and first.score.categories[0].present == 1


def test_owner_rejection_remains_distinct_from_proposed_and_provider_error(stored):
    class Rejected:
        def supports(self, _model):
            return False
    protocol, _, provider, runner = setup(stored, Rejected(), repetitions=1)
    result = runner.step(stored.principal, protocol.manifest.suite_id)
    assert result.status == 'complete' and not result.passed
    assert result.observations[0].observation.status == 'rejected' and provider.calls == 0
    assert json.loads(result.observations[0].observation.payload_json) == {
        'status': 'policy_rejected', 'reason_code': 'provider_or_profile_mismatch'}


def test_read_grants_and_frozen_adapter_mode_are_checked_before_work(stored):
    protocol, _, provider, runner = setup(stored, FixtureProvider('abstain'), mode='live')
    reader = replace(stored.principal, actions=frozenset({'read_attempts'}))
    assert runner.read(reader, protocol.manifest.suite_id).status == 'pending'
    with pytest.raises(PermissionError):
        runner.step(reader, protocol.manifest.suite_id)
    with pytest.raises(ValueError, match='evaluation_live_adapter_unconfigured'):
        runner.step(stored.principal, protocol.manifest.suite_id)
    assert provider.calls == 0
    with stored.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.dispatches WHERE tenant_id=:tenant AND project_id=:project'),
            {'tenant': stored.principal.scope.tenant_id, 'project': stored.principal.scope.project_id}).scalar_one() == 0


def test_valid_proposed_output_is_scored_against_the_pinned_independent_label(stored):
    protocol, _, _, runner = setup(stored, FixtureProvider('proposal'), repetitions=1, assertions=[{
        'assertion_id': 'allowed-action', 'pointer': '/action', 'operation': 'equals',
        'expected_json': '"propose_knowledge_change"'}])
    result = runner.step(stored.principal, protocol.manifest.suite_id)
    assert result.passed and result.observations[0].observation.status == 'proposed'


def test_independent_adversarial_rubric_can_expect_an_owner_rejection(stored):
    class Unsupported:
        def supports(self, _model):
            return False
    protocol, _, provider, runner = setup(stored, Unsupported(), repetitions=1, assertions=[{
        'assertion_id': 'rejection', 'pointer': '/reason_code', 'operation': 'equals',
        'expected_json': '"provider_or_profile_mismatch"'}])
    result = runner.step(stored.principal, protocol.manifest.suite_id)
    assert result.passed and result.observations[0].observation.status == 'rejected' and provider.calls == 0
