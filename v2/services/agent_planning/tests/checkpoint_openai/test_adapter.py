import json
import time
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.checkpoint_input import CheckpointEnvelope
from amphora_agent_planning.checkpoint_openai import CheckpointOpenAI
from amphora_agent_planning.checkpoint_openai.configuration import (
    LiveCheckpointSettings,
)
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.providers.port import ProviderUnavailable
from amphora_agent_planning.supervision_scheduling.configuration import (
    WorkerConfiguration,
)

from ..campaign_context.test_selection import request
from ..checkpoint_input.test_profile import live_plan
from ..openai_provider.test_adapter import response


def source(**limits):
    selected = live_plan()
    value = selected.request.document().model_dump(mode='json')
    value['context']['limits'].update(max_attempts=1, max_output_tokens=2048, total_tokens=67584,
        total_accounting_units=500000000, accounting_unit='usd_nanodollars', **limits)
    return replace(selected, request=request(value))


def test_original_packet_is_the_exact_transmitted_body_and_deadline_is_narrowed():
    selected = source()
    packet = prepare(selected).packet
    calls, configurations = [], []
    def factory(key, **settings):
        assert key == 'test-only-not-a-key'
        configurations.append(settings)
        return SimpleNamespace(send=lambda raw: calls.append(raw) or response())
    adapter = CheckpointOpenAI('test-only-not-a-key', timeout_seconds=45, transport_factory=factory)
    assert not calls
    assert adapter.supports(selected.request.document().context.model)
    result = adapter.reply(AttemptBinding(selected.request, 1), packet.canonical,
                           deadline_unix_ms=int(time.time()*1000)+5500)
    assert calls == [CheckpointEnvelope.bind(selected.request, packet.canonical).body]
    assert 1 <= configurations[-1]['timeout_seconds'] <= 5
    assert configurations[-1]['maximum_body_bytes'] == 65536
    assert result.usage.accounting_units == 300000 and b''.join(result.chunks)
    assert 'test-only-not-a-key' not in repr(adapter)
    assert not adapter.supports(selected.request.document().context.model.model_copy(update={'model_id': 'other'}))


@pytest.mark.parametrize('fault', ['deadline', 'fractional_deadline', 'packet', 'underbound', 'cost_unit'])
def test_invalid_input_and_expired_deadline_never_send(fault):
    selected = source()
    packet = prepare(selected).packet.canonical
    deadline = int(time.time()*1000)+10000
    if fault == 'deadline': deadline = 0
    if fault == 'fractional_deadline': deadline = 0.5
    if fault == 'packet': packet += b'\n'
    if fault in {'underbound', 'cost_unit'}:
        raw = selected.request.document().model_dump(mode='json')
        if fault == 'underbound': raw['context']['limits']['max_input_tokens'] = 100
        else: raw['context']['limits']['accounting_unit'] = 'invented'
        selected = replace(selected, request=request(raw))
        from amphora_agent_planning.campaign_context.records import canonical
        value = json.loads(packet)
        value['untrusted_context']['request'] = raw
        packet = canonical(value)
    calls = []
    adapter = CheckpointOpenAI('test-only', transport_factory=lambda *_a, **_k:
        SimpleNamespace(send=lambda raw: calls.append(raw)))
    with pytest.raises((ValueError, ProviderUnavailable)):
        adapter.reply(AttemptBinding(selected.request, 1), packet, deadline_unix_ms=deadline)
    assert not calls


def test_explicit_live_configuration_requires_egress_key_and_matching_provider():
    value = {'database_url_env': 'DB', 'actor_id': 'actor', 'scope': {'tenant_id': 't', 'project_id': 'p'},
        'publisher_id': 'publisher', 'data': {'endpoint': 'http://127.0.0.1:1', 'token_env': 'TOKEN'},
        'runtime': {'endpoint': 'http://127.0.0.1:2', 'token_env': 'TOKEN'}, 'templates': []}
    assert WorkerConfiguration.model_validate_json(json.dumps(value)).provider == 'disabled'
    value['provider'] = 'openai_checkpoint_v1'
    with pytest.raises(ValueError, match='checkpoint_live_configuration'):
        WorkerConfiguration.model_validate_json(json.dumps(value))
    value['live'] = {'key_env': 'KEY', 'egress': 'approved_synthetic_engineering_only'}
    config = WorkerConfiguration.model_validate_json(json.dumps(value))
    with pytest.raises(ValueError, match='checkpoint_live_templates_missing'):
        config.live.provider([])
    value['provider'] = 'fixture_abstain'
    with pytest.raises(ValueError, match='checkpoint_live_configuration'):
        WorkerConfiguration.model_validate_json(json.dumps(value))
    with pytest.raises(ValueError):
        LiveCheckpointSettings(key_env='KEY', egress='all_data')
