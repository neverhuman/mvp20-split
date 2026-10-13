import json
import time
from types import SimpleNamespace
import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.curation_budget import ceiling
from amphora_agent_planning.curation_openai.adapter import CurationOpenAI
from amphora_agent_planning.curation_openai.configuration import LiveCurationSettings
from amphora_agent_planning.curation_openai.window import CurationResponseWindow
from amphora_agent_planning.openai_provider.http import OpenAIHTTP
from amphora_agent_planning.curation_execution.executor import CurationExecutor
from .test_adapter import source
from ..openai_provider.test_adapter import response


def test_extended_window_preserves_default_and_exact_scope(monkeypatch):
    scope=source().request.document().reference.scope
    with pytest.raises(ValueError,match='curation_provider_timeout'):
        CurationResponseWindow.bind('standard-v1',61,scope)
    with pytest.raises(ValueError,match='curation_deadline_scope'):
        CurationResponseWindow.bind('scientific-v1',180,scope)
    monkeypatch.setattr(ceiling,'REVIEWED_DEMO',(scope.tenant_id,scope.project_id))
    window=CurationResponseWindow.bind('scientific-v1',180,scope)
    assert window.maximum==180
    for seconds in (0,181,True,1.5):
        with pytest.raises(ValueError):CurationResponseWindow.bind('scientific-v1',seconds,scope)
    with pytest.raises(ValueError,match='curation_deadline_model'):
        window.require_model(source(version='9').request.document().context.model)


def test_one_v10_send_clamps_extended_window_to_remaining_deadline(monkeypatch):
    selected=source(version='10',max_input_tokens=196608,max_output_tokens=16384,total_tokens=212992)
    scope=selected.request.document().reference.scope
    monkeypatch.setattr(ceiling,'REVIEWED_DEMO',(scope.tenant_id,scope.project_id))
    calls=[];settings=[]
    def factory(key,**options):
        settings.append(options)
        return SimpleNamespace(send=lambda raw:calls.append(raw) or response())
    adapter=CurationOpenAI('test-only',scope=scope,egress='approved_synthetic_engineering_only',
        timeout_seconds=180,deadline_profile='scientific-v1',transport_factory=factory)
    adapter.reply(AttemptBinding(selected.request,1),prepare(selected).packet.canonical,
        deadline_unix_ms=int(time.time()*1000)+90500)
    assert len(calls)==1
    assert 89<=settings[-1]['timeout_seconds']<=90
    assert settings[-1]['timeout_profile']=='curation-scientific-v1'
    assert settings[-1]['maximum_body_bytes']==262144


def test_explicit_transport_and_executor_profile_needed_for_longer_wait():
    with pytest.raises(ValueError,match='openai_timeout'):OpenAIHTTP('test-only',timeout_seconds=180)
    assert OpenAIHTTP('test-only',timeout_seconds=180,timeout_profile='curation-scientific-v1').timeout==180
    with pytest.raises(ValueError):OpenAIHTTP('test-only',timeout_seconds=181,timeout_profile='curation-scientific-v1')
    with pytest.raises(ValueError,match='curation_execution_timeout'):CurationExecutor(None,None,None,timeout_seconds=180)
    assert CurationExecutor(None,None,None,timeout_seconds=180,timeout_ceiling=180).timeout==180
    with pytest.raises(ValueError):CurationExecutor(None,None,None,timeout_seconds=181,timeout_ceiling=180)


def test_configuration_requires_explicit_scientific_window(monkeypatch):
    scope=source().request.document().reference.scope
    value={'key_env':'NO_KEY','scope':scope.model_dump(mode='json'),
        'egress':'approved_synthetic_engineering_only','timeout_seconds':180}
    with pytest.raises(ValueError):LiveCurationSettings.model_validate_json(json.dumps(value))
    monkeypatch.setattr(ceiling,'REVIEWED_DEMO',(scope.tenant_id,scope.project_id))
    settings=LiveCurationSettings.model_validate_json(json.dumps(dict(value,deadline_profile='scientific-v1')))
    assert settings.window.maximum==180
