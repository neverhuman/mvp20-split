"""Actual SQL/HTTP authorization, bounded pages and resnapshot failures."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.inspection.cursors import CursorCodec
from amphora_campaign_runtime.inspection.history import RuntimeHistory
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_campaign_runtime.supervision_api import SupervisorRecording
from amphora_campaign_runtime.supervision_inspection import SupervisorInspection
from amphora_contracts_supervision import (
    CheckpointContextPage,
    CheckpointInspectionPage,
    CheckpointRequestPage,
    CheckpointResponsePage,
)
from fastapi.testclient import TestClient

from ..supervision_resolution.support import record_response, setup
from .test_reads import KEY

READ = 'inspection-read-only-synthetic-token-000000000000'
DENIED = 'inspection-denied-synthetic-token-00000000000000'
FOREIGN = 'inspection-foreign-synthetic-token-0000000000000'


def configured(graph):
    actor, ref, slot, preparer, original, _ = setup(graph)
    reader = replace(actor, actor_id='inspector', actions=frozenset({'read'}))
    foreign = replace(reader, scope=actor.scope.model_copy(update={'project_id': 'unknown-project'}))
    credentials = RuntimeCredentials([(READ, reader), (DENIED, replace(reader, actions=frozenset())), (FOREIGN, foreign)])
    history = RuntimeHistory(graph.env.engine, CursorCodec(KEY))
    recording = SupervisorRecording(preparer.journal)
    app = create_app(graph.env.service, credentials, history=history, supervision=recording)
    return TestClient(app), (actor, ref, slot, preparer, original), credentials, recording


def get(http, path, *, token=READ, params=None):
    return http.get(path, params=params, headers={'Authorization': 'Bearer ' + token})


def test_configured_read_only_inspector_uses_public_pages_and_refresh_protocol(graph_env):
    http, values, _, _ = configured(graph_env)
    actor, ref, slot, preparer, original = values
    path = f'/v1/supervision/runs/{ref.run_id}/checkpoints'
    first = get(http, path)
    assert first.status_code == 200
    root = CheckpointInspectionPage.model_validate_json(first.content)
    params = {'snapshot_token': root.snapshot.snapshot_token}
    requests_path = path + f'/{ref.decision_id}/requests'
    requests = get(http, requests_path, params=params)
    assert requests.status_code == 200
    assert CheckpointRequestPage.model_validate_json(requests.content).total == 1
    selected = requests_path + '/' + original.frame.request_sha256
    context = get(http, selected + '/context', params=params)
    assert context.status_code == 200 and CheckpointContextPage.model_validate_json(context.content).total == 3
    responses = get(http, selected + '/responses', params=params)
    assert responses.status_code == 200 and CheckpointResponsePage.model_validate_json(responses.content).total == 0
    record_response(actor, ref, slot, preparer, original)
    stale = get(http, requests_path, params=params)
    assert stale.status_code == 409 and stale.json() == {'reason_code': 'snapshot_unavailable', 'resnapshot': True}
    fresh = get(http, path).json()
    assert fresh['snapshot']['epoch'] != root.snapshot.epoch
    assert http.get('/openapi.json').json()['paths'][
        '/v1/supervision/runs/{run_id}/checkpoints']['get']['security']


def test_http_scope_permission_and_query_bounds_are_explicit(graph_env):
    http, values, _, _ = configured(graph_env)
    ref = values[1]
    path = f'/v1/supervision/runs/{ref.run_id}/checkpoints'
    assert http.get(path).status_code == 401
    assert get(http, path, token=DENIED).status_code == 403
    assert get(http, path, token=FOREIGN).status_code == 404
    for params in ({'limit': 11}, {'cursor': 'x' * 4097}, {'scope': 'foreign'}, [('limit', 1), ('limit', 2)]):
        assert get(http, path, params=params).status_code == 422
    assert get(http, path + f'/{ref.decision_id}/requests').status_code == 422
    token = get(http, path).json()['snapshot']['snapshot_token']
    bad = get(http, path + f'/{ref.decision_id}/requests', params={'snapshot_token': token + 'bad'})
    assert bad.status_code == 409 and bad.json()['resnapshot']


def test_paged_routes_require_inspection_and_supervision_configuration(graph_env):
    _, values, credentials, recording = configured(graph_env)
    path = f'/v1/supervision/runs/{values[1].run_id}/checkpoints'
    assert TestClient(create_app()).get(path).status_code == 404
    only_recording = TestClient(create_app(graph_env.env.service, credentials, supervision=recording))
    assert get(only_recording, path).status_code == 404
    only_history = TestClient(create_app(graph_env.env.service, credentials,
        history=RuntimeHistory(graph_env.env.engine, CursorCodec(KEY))))
    assert get(only_history, path).status_code == 404


@pytest.mark.parametrize('fault', ['corrupt', 'oversized'])
def test_integrity_errors_are_redacted_at_read_boundary(graph_env, monkeypatch, fault):
    http, values, _, _ = configured(graph_env)
    def broken(*_args, **_kwargs):
        if fault == 'oversized':
            return SimpleNamespace(model_dump_json=lambda: 'x' * 262145)
        raise ValueError('private-invalid-row-content')
    monkeypatch.setattr(SupervisorInspection, 'checkpoints', broken)
    result = get(http, f'/v1/supervision/runs/{values[1].run_id}/checkpoints')
    assert result.status_code == 503
    assert result.json() == {'reason_code': 'supervision_inspection_unavailable'}
