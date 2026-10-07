"""Configured worker with actual SQL, scripted Data and intercepted provider transport."""

import hashlib
import json
import time

import pytest
from amphora_agent_planning.campaign_packet_profiles import reviewed_instructions
from amphora_agent_planning.checkpoint_input import (
    CheckpointEnvelope,
    checkpoint_tokenizer_reference,
)
from amphora_agent_planning.checkpoint_openai import CheckpointOpenAI
from amphora_agent_planning.openai_provider.http import OpenAIHTTP
from amphora_agent_planning.supervision_intake import SupervisionIntake
from amphora_agent_planning.supervision_scheduling.configuration import CheckpointHost
from amphora_contracts_planning import CheckpointDraft

from ..checkpoint_budget.test_journal import entry
from ..checkpoint_input.test_profile import MODEL
from ..supervision_execution.test_context import prepared
from ..supervision_execution.test_worker import Data
from ..supervision_intake.test_checkpoints import command
from ..supervision_scheduling.test_configuration import configuration

pytestmark = pytest.mark.postgres


def worker_configuration(stored, tmp_path, monkeypatch, version="1"):
    data = Data()
    def configure(original):
        context = original['context']
        context['entries'], context['omissions'] = [], []
        context['model'].update(provider_id='openai', model_id=MODEL, model_revision=MODEL,
            tokenizer=checkpoint_tokenizer_reference(version).model_dump(mode='json'), context_window_tokens=400000)
        context['limits'].update(max_input_tokens=65536, max_output_tokens=2048, total_tokens=67584,
            max_attempts=1, total_accounting_units=500000000, accounting_unit='usd_nanodollars')
        for name, ref in [('objective', context['objective']), ('policy', context['policy']),
                         ('model', context['model']['configuration']), ('prompt', context['prompt'])]:
            body = reviewed_instructions() if name == 'prompt' else b'Synthetic engineering only.'
            ref.update(sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body))
            data.bodies[ref['artifact_id']] = body
    actor, intake, ref, raw, templates = prepared(actor=stored.principal, configure=configure,
        deadline=int(time.time()*1000)+60000, per_attempt_units=58368000)
    data.bodies[ref.artifact_id] = raw
    assert SupervisionIntake(stored.engine).receive(actor, command(intake.document())).outcome.status == 'recorded'
    path, value = configuration(stored, tmp_path, monkeypatch)
    budget_ref, template = next(iter(templates._entries.values()))
    (tmp_path/'template.json').write_bytes(template.canonical)
    value.update(provider='openai_checkpoint_v1', live={'key_env': 'CHECKPOINT_TEST_KEY',
        'egress': 'approved_synthetic_engineering_only'},
        templates=[{'reference': budget_ref.model_dump(mode='json'), 'path': 'template.json'}])
    path.write_text(json.dumps(value), encoding='utf-8')
    monkeypatch.setenv('CHECKPOINT_TEST_KEY', 'synthetic-not-a-provider-key')
    return path, intake, data


@pytest.mark.parametrize('version', ['1', '2'])
@pytest.mark.parametrize('exhausted', [False, True])
def test_configured_worker_retains_exact_input_and_replays_without_new_call(stored, tmp_path, monkeypatch, exhausted, version):
    path, intake, data = worker_configuration(stored, tmp_path, monkeypatch, version)
    calls = []
    def send(_self, body):
        calls.append(body)
        draft = CheckpointDraft(authority='proposal_only', scientific_authority='not_established', action='abstain',
            rationale='Synthetic provider fixture.', decision_scope=intake.planning.document().decision_scope,
            candidate=None, evidence_requests=(), alternatives=(), unresolved=())
        return json.dumps({'model': MODEL, 'status': 'completed', 'usage': {'input_tokens': 100, 'output_tokens': 50},
            'output': [{'type': 'message', 'role': 'assistant', 'content': [
                {'type': 'output_text', 'text': draft.model_dump_json()}]}]}).encode()
    monkeypatch.setattr(OpenAIHTTP, 'send', send)
    host = CheckpointHost.load(path)
    try:
        worker = host.poller.worker
        assert isinstance(worker.provider, CheckpointOpenAI) and not calls
        worker.data = data  # Scripted public Data port, never an actual-owner claim.
        if exhausted:
            from amphora_agent_planning.persistence.budget import BudgetLedger
            BudgetLedger(stored.engine).reserve(stored.principal, *entry(stored, 'earlier', units=500000000))
        engagement = intake.planning.document().reference.engagement_id
        outcome = worker.run(stored.principal, engagement)
        assert outcome.stop_reason == ('accounting_budget_exhausted' if exhausted else 'abstained')
        assert len(calls) == (0 if exhausted else 1)
        if not exhausted:
            retained = worker.preparations.read(stored.principal, intake.planning.document().reference)
            assert calls[0] == CheckpointEnvelope.bind(intake.planning, retained.record.packet.canonical).body
    finally:
        host.close()
    # Reload configuration and engine, revoke source access, preserve original completion.
    data.denied = True
    host = CheckpointHost.load(path)
    try:
        host.poller.worker.data = data
        assert host.poller.worker.run(stored.principal, engagement) == outcome
        assert len(calls) == (0 if exhausted else 1)
    finally:
        host.close()
