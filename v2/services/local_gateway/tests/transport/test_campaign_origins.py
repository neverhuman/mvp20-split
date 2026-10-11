"""Only the bounded, exact Planning provenance read is added."""

import http.client
import json
from types import SimpleNamespace

import pytest
from amphora_local_gateway.configuration import GatewayError, Peer
from amphora_local_gateway.proxy import Route, forward

PATH = '/api/planning/v1/campaign-origins/draft:1?revision=1&content_sha256=' + 'a' * 64


def test_origin_route_preserves_exact_owner_query():
    route = Route.parse(PATH)
    assert route.campaign_origin and route.target == PATH.removeprefix('/api/planning')


@pytest.mark.parametrize('path', [PATH + '&latest=true', PATH + '&revision=1',
    PATH.replace('revision=1', 'revision=01'), PATH.replace('revision=1', 'revision=9007199254740992'),
    PATH.replace('/draft:1?', '/draft:1/extra?'), PATH.replace('campaign-origins/', 'campaign-origins-extra/'),
    '/api/planning/v1/campaign-origins', '/api/planning/v1/campaign-origins/draft'])
def test_reject_broad_or_ambiguous_origin_routes(path):
    with pytest.raises(GatewayError):
        Route.parse(path)


@pytest.mark.parametrize('method,body', [('POST', b'{}'), ('GET', b'{}')])
def test_origin_has_no_write_or_body_channel(method, body):
    with pytest.raises(GatewayError, match='gateway_campaign_origin_read_only'):
        forward(Peer(1234, 'private-peer-token'), Route.parse(PATH), method, body, 'test')


@pytest.mark.parametrize('code,expected', [('campaign_origin_not_recorded', 'campaign_origin_not_recorded'),
    ('campaign_origin_response_limit', 'campaign_origin_response_limit'), ('private-details', None)])
def test_only_named_provenance_failures_cross_gateway(monkeypatch, code, expected):
    raw = json.dumps({'reason_code': code, 'secret': 'private-value'}).encode()
    class Connection:
        def __init__(self, *args, **kwargs): pass
        def request(self, *args, **kwargs): pass
        def getresponse(self): return SimpleNamespace(status=404, read=lambda bound: raw[:bound])
        def close(self): pass
    monkeypatch.setattr(http.client, 'HTTPConnection', Connection)
    status, _, body = forward(Peer(1234, 'private-peer-token'), Route.parse(PATH), 'GET', b'', 'test')
    assert status == 404 and b'private-value' not in body
    assert json.loads(body) == ({'reason_code': expected} if expected else {'error': 'owner_request_rejected'})


def test_provenance_response_has_its_own_256kib_limit(monkeypatch):
    class Connection:
        def __init__(self, *args, **kwargs): pass
        def request(self, *args, **kwargs): pass
        def getresponse(self):
            return SimpleNamespace(status=200, getheader=lambda name: '262145', read=lambda bound: b'x' * bound)
        def close(self): pass
    monkeypatch.setattr(http.client, 'HTTPConnection', Connection)
    with pytest.raises(GatewayError, match='gateway_response_bound'):
        forward(Peer(1234, 'private-peer-token'), Route.parse(PATH), 'GET', b'', 'test')
