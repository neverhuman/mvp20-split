import json
import time
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.curation_input import CurationEnvelope
from amphora_agent_planning.curation_openai import CurationOpenAI
from amphora_agent_planning.curation_openai.configuration import LiveCurationSettings
from amphora_agent_planning.providers.port import ProviderUnavailable

from ..campaign_context.test_selection import request
from ..curation_input.test_profile import curation_plan
from ..openai_provider.test_adapter import response


def source(version="1", **changes):
    plan = curation_plan(maximum=262144, version=version)
    value = plan.request.document().model_dump(mode='json')
    limits = dict(max_attempts=1, max_output_tokens=8192, total_tokens=270336,
                  total_accounting_units=250000000, accounting_unit='usd_nanodollars')
    limits.update(changes)
    value['context']['limits'].update(limits)
    return replace(plan, request=request(value))


@pytest.mark.parametrize("version", ["1", "2", "3", "4"])
def test_one_exact_send_with_narrowed_deadline_and_closed_scope(version):
    selected = source(version=version)
    packet = prepare(selected).packet
    calls, settings = [], []
    def factory(key, **configuration):
        assert key == 'test-only-not-a-key'
        settings.append(configuration)
        return SimpleNamespace(send=lambda raw: calls.append(raw) or response())
    adapter = CurationOpenAI('test-only-not-a-key', scope=selected.request.document().reference.scope,
        egress='approved_synthetic_engineering_only', transport_factory=factory)
    assert not calls and adapter.supports(selected.request.document().context.model)
    reply = adapter.reply(AttemptBinding(selected.request, 1), packet.canonical,
                          deadline_unix_ms=int(time.time() * 1000) + 5500)
    assert calls == [CurationEnvelope.bind(selected.request, packet.canonical).body]
    assert 1 <= settings[-1]['timeout_seconds'] <= 5
    assert settings[-1]['maximum_body_bytes'] == 262144
    assert reply.usage.accounting_units == 300000 and b''.join(reply.chunks)
    assert 'test-only-not-a-key' not in repr(adapter)


@pytest.mark.parametrize('fault', ['scope', 'deadline', 'fractional_deadline', 'packet', 'cost_unit', 'attempts'])
def test_unapproved_scope_or_invalid_input_never_sends(fault):
    selected = source()
    packet = prepare(selected).packet.canonical
    scope = selected.request.document().reference.scope
    deadline = int(time.time() * 1000) + 10000
    if fault == 'scope': scope = scope.model_copy(update={'project_id': 'other'})
    if fault == 'deadline': deadline = 0
    if fault == 'fractional_deadline': deadline = 0.5
    if fault == 'packet': packet += b'\n'
    if fault == 'cost_unit': selected = source(accounting_unit='other')
    if fault == 'attempts': selected = source(max_attempts=2)
    calls = []
    adapter = CurationOpenAI('test-only', scope=scope, egress='approved_synthetic_engineering_only',
        transport_factory=lambda *_a, **_k: SimpleNamespace(send=lambda raw: calls.append(raw)))
    with pytest.raises((ValueError, ProviderUnavailable)):
        adapter.reply(AttemptBinding(selected.request, 1), packet, deadline_unix_ms=deadline)
    assert not calls


def test_timeout_has_no_automatic_transport_retry():
    selected = source()
    calls = []
    def send(raw):
        calls.append(raw)
        raise TimeoutError('scripted')
    adapter = CurationOpenAI('test-only', scope=selected.request.document().reference.scope,
        egress='approved_synthetic_engineering_only', transport_factory=lambda *_a, **_k: SimpleNamespace(send=send))
    with pytest.raises(TimeoutError):
        adapter.reply(AttemptBinding(selected.request, 1), prepare(selected).packet.canonical,
                      deadline_unix_ms=int(time.time() * 1000) + 10000)
    assert len(calls) == 1


def test_operator_configuration_cannot_omit_scope_or_widen_egress():
    scope = source().request.document().reference.scope.model_dump(mode='json')
    value = {'key_env': 'CURATION_KEY', 'scope': scope, 'egress': 'approved_synthetic_engineering_only'}
    settings = LiveCurationSettings.model_validate_json(json.dumps(value))
    with pytest.raises(ValueError, match='curation_live_policies_missing'): settings.provider([])
    with pytest.raises(ValueError): LiveCurationSettings.model_validate_json(json.dumps({**value, 'egress': 'all'}))
    del value['scope']
    with pytest.raises(ValueError): LiveCurationSettings.model_validate_json(json.dumps(value))


def test_additive_transport_limit_does_not_widen_existing_profiles():
    from amphora_agent_planning.openai_provider.http import OpenAIHTTP
    connections = []
    def connection(*args, **kwargs):
        connections.append((args, kwargs))
        raise AssertionError('oversized request must not open a connection')
    legacy = OpenAIHTTP('test-only', maximum_body_bytes=65536, connection_factory=connection)
    curation = OpenAIHTTP('test-only', maximum_body_bytes=262144, connection_factory=connection)
    with pytest.raises(ValueError, match='openai_http_body'): legacy.send(b' ' * 65537)
    with pytest.raises(ValueError, match='openai_http_body'): curation.send(b' ' * 262145)
    assert not connections


@pytest.mark.parametrize('status,content', [('incomplete', None), ('completed', [{'type': 'refusal', 'refusal': 'no'}])])
@pytest.mark.parametrize('version', ['3', '4'])
def test_structured_refusal_and_incomplete_never_become_accepted_output(status, content, version):
    selected = source(version=version)
    calls = []
    def send(raw):
        calls.append(raw)
        return response(status=status, content=content)
    adapter = CurationOpenAI('test-only', scope=selected.request.document().reference.scope,
        egress='approved_synthetic_engineering_only', transport_factory=lambda *_a, **_k: SimpleNamespace(send=send))
    reply = adapter.reply(AttemptBinding(selected.request, 1), prepare(selected).packet.canonical,
                          deadline_unix_ms=int(time.time() * 1000) + 10000)
    with pytest.raises(TimeoutError, match='openai_output_incomplete'):
        b''.join(reply.chunks)
    assert len(calls) == 1 and reply.usage.certainty == 'reported'
    assert adapter.last_response.status == status
    assert adapter.last_response.refused is (status == 'completed')
    assert adapter.last_transport_failure is None
