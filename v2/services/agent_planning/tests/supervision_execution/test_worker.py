"""Real Planning SQL with scripted Data and deterministic packet-aware provider."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from amphora_agent_planning.campaign_packet_profiles import (
    fixture_tokenizer_reference,
    reviewed_instructions,
)
from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.supervision_execution.worker import CheckpointWorker
from amphora_agent_planning.supervision_intake import SupervisionIntake
from sqlalchemy import text

from ..campaign_output.test_output import output
from ..supervision_intake.test_checkpoints import command
from .test_context import prepared

pytestmark = pytest.mark.postgres


class Data:
    def __init__(self):
        self.bodies, self.calls, self.denied = {}, [], False

    def artifact(self, ref, budget):
        self.calls.append(ref.artifact_id)
        if self.denied:
            raise ValueError('source_access_denied')
        return ref

    def content(self, ref, budget):
        return self.bodies[ref.artifact_id]


class Provider:
    def __init__(self, variant='abstain'):
        self.variant, self.calls = variant, []

    def supports(self, model):
        return True

    def reply(self, binding, packet, *, deadline_unix_ms):
        self.calls.append((binding, packet, deadline_unix_ms))
        value = output('abstain')
        value.update(schema_version='2', decision_scope=binding.request.document().decision_scope)
        for unresolved in value['unresolved']:
            for field in ('question', 'need'):
                unresolved[field]['scope'] = binding.request.document().reference.scope.model_dump(mode='json')
        return ProviderReply([b'bad' if self.variant == 'invalid' else json.dumps(value).encode()], unknown_usage())


def setup(s, *, maximum=200000, variant='abstain', extra_count=0, attempts=2, configure_request=None):
    data, provider = Data(), Provider(variant)
    def configure(original):
        context = original['context']
        context['entries'], context['omissions'] = [], []
        context['model']['tokenizer'] = fixture_tokenizer_reference().model_dump(mode='json')
        context['model']['context_window_tokens'] = maximum + 4096
        context['limits'].update(max_input_tokens=maximum, max_output_tokens=4096,
            total_tokens=2 * (maximum + 4096), total_accounting_units=120, max_attempts=attempts)
        for name, ref in [('objective', context['objective']), ('policy', context['policy']),
                         ('model', context['model']['configuration']), ('prompt', context['prompt'])]:
            body = reviewed_instructions() if name == 'prompt' else name.encode()
            ref.update(sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body))
            data.bodies[ref['artifact_id']] = body
        for index in range(extra_count):
            ref = dict(context['objective'], artifact_id=f'extra-{index}')
            context['entries'].append({'artifact': ref, 'role': 'source', 'required': True})
            data.bodies[ref['artifact_id']] = b'objective'
        if configure_request is not None:
            configure_request(original, data)
    with s.engine.connect() as conn:
        deadline = conn.execute(text('SELECT floor(extract(epoch FROM clock_timestamp())*1000)::bigint+60000')).scalar_one()
    actor, intake, ref, raw, templates = prepared(actor=s.principal, configure=configure, deadline=deadline)
    data.bodies[ref.artifact_id] = raw
    assert SupervisionIntake(s.engine).receive(actor, command(intake.document())).outcome.status == 'recorded'
    worker = CheckpointWorker(s.engine, data, templates, provider, timeout_seconds=30)
    return worker, data, provider, intake


def test_exact_packet_call_and_replacement_replay_ignore_revoked_processing(stored):
    worker, data, provider, intake = setup(stored)
    engagement = intake.planning.document().reference.engagement_id
    first = worker.run(stored.principal, engagement)
    assert first.stop_reason == 'abstained' and len(provider.calls) == 1
    retained = worker.preparations.read(stored.principal, intake.planning.document().reference)
    assert provider.calls[0][1] == retained.record.packet.canonical
    assert 0 < provider.calls[0][2] <= intake.document().deadline_unix_ms
    data.denied = True
    reads = len(data.calls)
    replacement = CheckpointWorker(stored.engine, data, None, None, timeout_seconds=1)
    assert replacement.run(stored.principal, engagement) == first
    assert len(data.calls) == reads and len(provider.calls) == 1


@pytest.mark.parametrize('denied,maximum,reason', [(True, 200000, 'required_artifact_unavailable'),
    (False, 100, 'required_input_limit')])
def test_preparation_failure_makes_no_dispatch(stored, denied, maximum, reason):
    worker, data, provider, intake = setup(stored, maximum=maximum)
    data.denied = denied
    result = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    assert result.stop_reason == reason and not result.attempts and not provider.calls
    assert worker.preparations.read(stored.principal, intake.planning.document().reference) is None


def test_reserved_preparation_is_not_a_continuing_permission(stored):
    worker, data, provider, intake = setup(stored)
    retained = worker._packet(stored.principal, intake)
    data.denied = True
    result = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    assert result.stop_reason == 'execution_processing_unavailable' and not provider.calls
    assert worker.preparations.read(stored.principal, intake.planning.document().reference).record == retained.preparation


def test_invalid_output_consumes_bounded_attempts_with_same_packet(stored):
    worker, data, provider, intake = setup(stored, variant='invalid')
    result = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    assert result.stop_reason == 'attempt_limit' and len(provider.calls) == 2
    assert provider.calls[0][1] == provider.calls[1][1]
    data.denied = True
    assert worker.run(stored.principal, intake.planning.document().reference.engagement_id) == result
    assert len(provider.calls) == 2


def test_pending_call_recovers_without_processing_or_second_provider(stored):
    worker, data, provider, intake = setup(stored)
    entered, release = Event(), Event()
    original = provider.reply
    def held(*args, **kwargs):
        entered.set()
        assert release.wait(10)
        return original(*args, **kwargs)
    provider.reply = held
    engagement = intake.planning.document().reference.engagement_id
    with ThreadPoolExecutor(max_workers=1) as pool:
        running = pool.submit(worker.run, stored.principal, engagement)
        try:
            assert entered.wait(10)
            reads = len(data.calls)
            data.denied = True
            replacement = CheckpointWorker(stored.engine, data, None, None, timeout_seconds=1)
            pending = replacement.run(stored.principal, engagement)
            assert pending.stop_reason == 'attempt_pending' and len(pending.attempts) == 1
            assert len(data.calls) == reads
        finally:
            release.set()
        result = running.result(10)
    assert result.stop_reason == 'abstained' and len(provider.calls) == 1


def test_revocation_between_issuance_and_provider_retains_uncertainty(stored, monkeypatch):
    worker, data, provider, intake = setup(stored)
    from amphora_agent_planning.persistence.dispatch import DispatchJournal
    original = DispatchJournal.issue
    def revoke(*args, **kwargs):
        ticket = original(*args, **kwargs)
        data.denied = True
        return ticket
    monkeypatch.setattr(DispatchJournal, 'issue', revoke)
    result = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    assert not provider.calls and len(result.attempts) == 1
    assert result.attempts[0].observation.document().status == 'unknown'
    assert result.stop_reason == 'execution_processing_unavailable'
