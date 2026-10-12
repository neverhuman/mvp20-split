import http.client
import json
from types import SimpleNamespace

import pytest
from amphora_local_gateway.configuration import GatewayError, Peer
from amphora_local_gateway.proxy import Route, forward


@pytest.mark.parametrize('path,method', [('/campaign-curations', 'POST'),
    ('/campaign-curations/receipts/query', 'POST'), ('/campaign-curations/curation:1', 'GET'),
    ('/capability-requests/request:1', 'GET'), ('/capability-requests/request:1/fulfillments', 'POST')])
def test_only_approved_method_and_path_pairs(path, method):
    route = Route.parse('/api/planning/v1' + path)
    assert route.curation.method == method
    route.curation.check(method, b'{}' if method == 'POST' else b'')
    with pytest.raises(GatewayError): route.curation.check('GET' if method == 'POST' else 'POST', b'')
    with pytest.raises(GatewayError): route.curation.check(method, b'x' * 262145)
    if method == 'GET':
        with pytest.raises(GatewayError): route.curation.check(method, b'{}')


@pytest.mark.parametrize('path', ['/campaign-curations-extra', '/campaign-curations/x/extra',
    '/campaign-curations/receipts/latest', '/capability-requests', '/capability-requests/x/verify',
    '/capability-requests/x/fulfillments/extra', '/capability-requests/x?latest=true',
    '/campaign-curations?scope=other', '/campaign-curations/a%2Fb', '/capability-requests/%252f'])
def test_unapproved_or_ambiguous_paths_reject_before_peer_access(path):
    with pytest.raises(GatewayError): Route.parse('/api/planning/v1' + path)


@pytest.mark.parametrize('code,expected', [('capability_request_not_recorded', 'capability_request_not_recorded'),
    ('curation_not_recorded', 'curation_not_recorded'), ('fulfillment_command_conflict', 'fulfillment_command_conflict'),
    ('private-diagnostic', None)])
def test_named_failures_preserve_meaning_without_private_details(monkeypatch, code, expected):
    raw = json.dumps({'reason_code': code, 'secret': 'private-value'}).encode()
    class Connection:
        def __init__(self, *args, **kwargs): pass
        def request(self, *args, **kwargs): pass
        def getresponse(self): return SimpleNamespace(status=404, read=lambda bound: raw[:bound])
        def close(self): pass
    monkeypatch.setattr(http.client, 'HTTPConnection', Connection)
    status, _, body = forward(Peer(1234, 'private-peer-token'),
        Route.parse('/api/planning/v1/capability-requests/gap'), 'GET', b'', 'test')
    assert status == 404 and b'private-value' not in body
    assert json.loads(body) == ({'reason_code': expected} if expected else {'error': 'owner_request_rejected'})


def test_curation_response_has_its_own_one_mib_bound(monkeypatch):
    class Connection:
        def __init__(self, *args, **kwargs): pass
        def request(self, *args, **kwargs): pass
        def getresponse(self): return SimpleNamespace(status=200, getheader=lambda name: '1048577')
        def close(self): pass
    monkeypatch.setattr(http.client, 'HTTPConnection', Connection)
    with pytest.raises(GatewayError, match='gateway_response_bound'):
        forward(Peer(1234, 'private-peer-token'), Route.parse('/api/planning/v1/campaign-curations/original'),
            'GET', b'', 'test')
