"""Exact authenticated route with scoped read authority and sanitized failures."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from amphora_agent_planning.supervision_api import Credentials, create_app

from .test_projection import origin_inputs, projection  # noqa: F401


@pytest.fixture
def http_case(projection, origin_inputs):
    calls = []
    state = SimpleNamespace(result=projection, error=None)
    def read(principal, draft):
        calls.append((principal, draft))
        if state.error is not None:
            raise state.error
        return state.result
    viewer = replace(origin_inputs[0], actor_id='viewer', actions=frozenset({'read_campaign_origin'}))
    credentials = Credentials((('v' * 32, viewer), ('w' * 32, origin_inputs[0])))
    app = create_app(SimpleNamespace(engine=None), credentials, campaign_origins=SimpleNamespace(read=read))
    client = TestClient(app)
    draft = projection.document().origin.draft
    url = f'/v1/campaign-origins/{draft.draft_id}?revision={draft.revision}&content_sha256={draft.content_sha256}'
    return SimpleNamespace(client=client, state=state, calls=calls, viewer=viewer, draft=draft, url=url,
                           headers={'Authorization': 'Bearer ' + 'v' * 32}, projection=projection)


def test_exact_public_read_preserves_canonical_bytes_and_viewer_identity(http_case):
    case = http_case
    response = case.client.get(case.url, headers=case.headers)
    assert response.status_code == 200 and response.content == case.projection.canonical
    assert response.headers['cache-control'] == 'no-store'
    assert case.calls == [(case.viewer, case.draft)]


@pytest.mark.parametrize('headers,status', [({}, 401), ({'Authorization': 'Bearer ' + 'w' * 32}, 403)])
def test_origin_grant_is_separate_and_denial_precedes_owner_read(http_case, headers, status):
    assert http_case.client.get(http_case.url, headers=headers).status_code == status
    assert not http_case.calls


@pytest.mark.parametrize('suffix', ['&revision=1', '&scope=foreign', '&latest=true'])
def test_query_aliases_and_duplicates_are_not_accepted(http_case, suffix):
    assert http_case.client.get(http_case.url + suffix, headers=http_case.headers).status_code == 422
    assert not http_case.calls


@pytest.mark.parametrize('query', ['', '?revision=1', '?revision=0&content_sha256=' + 'a' * 64,
    '?revision=01&content_sha256=' + 'a' * 64, '?revision=9007199254740992&content_sha256=' + 'a' * 64,
    '?revision=1&content_sha256=wrong'])
def test_all_exact_pins_required(http_case, query):
    path = http_case.url.split('?')[0]
    assert http_case.client.get(path + query, headers=http_case.headers).status_code == 422
    assert not http_case.calls


def test_missing_origin_does_not_infer_authorship(http_case):
    http_case.state.result = None
    response = http_case.client.get(http_case.url, headers=http_case.headers)
    assert response.status_code == 404 and response.json() == {'reason_code': 'campaign_origin_not_recorded'}


@pytest.mark.parametrize('error,status,code', [
    (ValueError('private history detail'), 409, 'campaign_origin_inconsistent'),
    (ValueError('origin_response_limit'), 422, 'campaign_origin_response_limit'),
    (PermissionError('private grant detail'), 403, 'planning_access_denied'),
])
def test_failures_are_bounded_and_sanitized(http_case, error, status, code):
    http_case.state.error = error
    response = http_case.client.get(http_case.url, headers=http_case.headers)
    assert response.status_code == status and response.json() == {'reason_code': code}


def test_route_has_no_mutation_or_backfill_surface(http_case):
    case = http_case
    assert case.client.post(case.url, headers=case.headers).status_code == 405
    assert case.client.get('/v1/campaign-origins', headers=case.headers).status_code == 404
    assert case.client.get('/v1/campaign-origins/backfill', headers=case.headers).status_code == 422
    assert case.client.request('GET', case.url, headers=case.headers, content=b'{}').status_code == 422
    assert not case.calls


def test_unconfigured_app_does_not_create_an_origin_service():
    with pytest.raises(ValueError, match='campaign_origins_require_configured_planning'):
        create_app(campaign_origins=object())
