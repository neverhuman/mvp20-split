"""Public reads distinguish immutable execution decisions from proposed responses."""

from dataclasses import replace

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.supervision_api import SupervisorRecording
from fastapi.testclient import TestClient

from ..supervision_resolution.support import record_response, save_report, setup

TOKEN = 'checkpoint-decision-read-synthetic-000000000000'
DENIED = 'checkpoint-decision-denied-synthetic-0000000000'
FOREIGN = 'checkpoint-decision-foreign-synthetic-000000000'


@pytest.mark.parametrize('kind', ['model_accepted', 'fallback', 'cancelled'])
def test_committed_decision_read_survives_api_replacement_without_acceptance(graph_env, kind):
    actor, ref, slot, preparer, original, resolver = setup(graph_env)
    reader = replace(actor, actions=frozenset({'read'}))
    foreign = replace(reader, scope=reader.scope.model_copy(update={'project_id': 'foreign-project'}))
    credentials = RuntimeCredentials([(TOKEN, reader), (FOREIGN, foreign),
        (DENIED, replace(actor, actions=frozenset({'supervise_accept'})))])
    path = f'/v1/supervision/decisions/{ref.run_id}/{ref.decision_id}'
    headers = {'Authorization': 'Bearer ' + TOKEN}

    def client():
        return TestClient(create_app(graph_env.env.service, credentials,
            supervision=SupervisorRecording(preparer.journal)))

    with client() as http:
        missing = http.get(path, headers=headers)
        assert missing.status_code == 404
        assert resolver.winners.read(actor, ref) is None
        assert http.get(path).status_code == 401
        assert http.get(path, headers={'Authorization': 'Bearer ' + DENIED}).status_code == 403
        assert http.get(path + '?scope=other', headers=headers).status_code == 422
        if kind == 'cancelled':
            command = graph_env.command('runtime.cancel', {'run_id': ref.run_id, 'reason_code': 'read_probe'})
            AuthorityCommands(graph_env.env.engine).cancel(actor, command)
            winner = resolver.winners.resolve(actor, ref)
        else:
            proposed = record_response(actor, ref, slot, preparer, original) if kind == 'model_accepted' else None
            # A recorded proposal is not an authoritative decision.
            assert http.get(path, headers=headers).status_code == 404
            save_report(resolver, actor, original, proposed)
            winner = resolver.resolve(actor, ref, original.frame.request_sha256)
        expected = winner.document().model_dump(mode='json')
        assert expected['outcome']['kind'] == kind
        response = http.get(path, headers=headers)
        assert response.status_code == 200 and response.json() == expected
        assert http.get(path, headers={'Authorization': 'Bearer ' + FOREIGN}).json() == missing.json()
        assert http.get('/v1/supervision/decisions/unknown/unknown', headers=headers).json() == missing.json()
        assert http.get('/openapi.json').json()['paths'][
            '/v1/supervision/decisions/{run_id}/{decision_id}']['get']['security']
    with client() as replacement:
        assert replacement.get(path, headers=headers).json() == expected
    assert resolver.winners.read(actor, ref) == winner
