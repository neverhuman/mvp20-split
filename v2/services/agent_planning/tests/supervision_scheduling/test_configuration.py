"""Explicit worker startup, disabled provider, exact templates and deterministic fixtures."""

import json
import subprocess
import sys
import time

import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.providers.port import ProviderUnavailable
from amphora_agent_planning.supervision_scheduling.configuration import CheckpointHost
from amphora_agent_planning.supervision_scheduling.fixture import CheckpointFixture
from amphora_contracts_planning import CheckpointDraft

from ..supervision_execution.test_budget_template import documents, reference, reviewed
from ..supervision_execution.test_worker import setup

pytestmark = pytest.mark.postgres


def configuration(stored, tmp_path, monkeypatch):
    monkeypatch.setenv('TEST_CHECKPOINT_PLANNING_DB', stored.engine.url.render_as_string(hide_password=False))
    monkeypatch.setenv('TEST_CHECKPOINT_PLANNING_TOKEN', 'synthetic-planning-token-000000000000000')
    peer = {'endpoint': 'http://127.0.0.1:1', 'token_env': 'TEST_CHECKPOINT_PLANNING_TOKEN'}
    raw = {'database_url_env': 'TEST_CHECKPOINT_PLANNING_DB', 'actor_id': stored.principal.actor_id,
        'scope': stored.principal.scope.model_dump(mode='json'), 'publisher_id': 'data-owner',
        'data': peer, 'runtime': peer, 'templates': []}
    path = tmp_path / 'planning-worker.json'
    path.write_text(json.dumps(raw), encoding='utf-8')
    return path, raw


def process(path, action):
    return subprocess.run([sys.executable, '-m', 'amphora_agent_planning.supervision_scheduling', action,
        '--config', str(path), '--seconds', '0.05', '--interval', '0.05'], capture_output=True,
        text=True, check=False, timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def test_process_restart_retains_disabled_provider_completion(stored, tmp_path, monkeypatch):
    worker, _, provider, intake = setup(stored)
    path, _ = configuration(stored, tmp_path, monkeypatch)
    assert process(path, 'check').returncode == 0
    first = process(path, 'run')
    assert first.returncode == 0 and json.loads(first.stdout)['execution'] == 1
    completion = worker.completions.read(stored.principal, intake.planning.document().reference.engagement_id)
    assert completion.report.document().stop_reason == 'provider_unconfigured'
    assert completion.report.document().attempts == () and provider.calls == []
    second = process(path, 'run')
    assert second.returncode == 0 and json.loads(second.stdout)['idle'] >= 1
    assert worker.completions.read(stored.principal, intake.planning.document().reference.engagement_id) == completion


@pytest.mark.parametrize('change', ['unknown_provider', 'missing_secret', 'role', 'oversized'])
def test_invalid_process_configuration_has_safe_failure(stored, tmp_path, monkeypatch, change):
    path, raw = configuration(stored, tmp_path, monkeypatch)
    if change == 'unknown_provider':
        raw['provider'] = 'live_unapproved'
    elif change == 'missing_secret':
        monkeypatch.delenv('TEST_CHECKPOINT_PLANNING_TOKEN')
    elif change == 'role':
        monkeypatch.setenv('TEST_CHECKPOINT_PLANNING_DB', stored.engine.url.set(username='planning_migrator').render_as_string(hide_password=False))
    if change == 'oversized':
        path.write_bytes(b' ' * 65537)
    else:
        path.write_text(json.dumps(raw), encoding='utf-8')
    result = process(path, 'check')
    assert result.returncode == 2 and result.stdout == ''
    assert 'durable state remains authoritative' in result.stderr
    assert 'synthetic-planning-token' not in result.stderr and 'postgresql' not in result.stderr


def test_explicit_exact_template_and_fixture_configuration(stored, tmp_path, monkeypatch):
    path, raw = configuration(stored, tmp_path, monkeypatch)
    original, record = documents(stored.principal)
    template = reviewed(record)
    ref = reference(template, original)
    (tmp_path / 'template.json').write_bytes(template.canonical)
    raw.update(provider='fixture_abstain', templates=[{'reference': ref.model_dump(mode='json'), 'path': 'template.json'}])
    path.write_text(json.dumps(raw), encoding='utf-8')
    host = CheckpointHost.load(path)
    try:
        assert host.poller.worker.templates.require(ref) == template
        assert isinstance(host.poller.worker.provider, CheckpointFixture)
    finally:
        host.close()
    (tmp_path / 'template.json').write_bytes(template.canonical + b' ')
    with pytest.raises(ValueError, match='noncanonical_budget_template'):
        CheckpointHost.load(path)


def test_fixture_is_bounded_and_has_no_scientific_authority(stored):
    _, _, _, intake = setup(stored)
    binding = AttemptBinding(intake.planning, 1)
    provider = CheckpointFixture('fixture_abstain')
    reply = provider.reply(binding, b'original-packet', deadline_unix_ms=int(time.time() * 1000) + 1000)
    draft = CheckpointDraft.model_validate_json(b''.join(reply.chunks))
    assert draft.decision_scope == binding.request.document().decision_scope
    assert draft.action == 'abstain' and draft.scientific_authority == 'not_established'
    bad = CheckpointFixture('fixture_invalid').reply(binding, b'packet', deadline_unix_ms=int(time.time() * 1000) + 1000)
    assert b''.join(bad.chunks) == b'{'
    with pytest.raises(ProviderUnavailable):
        provider.reply(binding, b'packet', deadline_unix_ms=0)
    with pytest.raises(ValueError, match='checkpoint_fixture_variant'):
        CheckpointFixture('live')
    model = binding.request.document().context.model
    assert provider.supports(model.model_copy(update={'provider_id': 'deterministic',
        'model_id': 'adversarial-fixture', 'model_revision': '1'}))
    assert not provider.supports(model.model_copy(update={'provider_id': 'other'}))
