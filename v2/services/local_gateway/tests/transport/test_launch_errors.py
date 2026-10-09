import http.client
import json
from types import SimpleNamespace
import pytest

from amphora_local_gateway.configuration import Peer
from amphora_local_gateway.proxy import Route, forward


@pytest.mark.parametrize('body,expected', [
    ({'reason_code': 'launch_slot_busy', 'secret': 'private-owner-value'}, {'reason_code': 'launch_slot_busy'}),
    ({'reason_code': 'private-owner-value'}, {'error': 'owner_request_rejected'}),
    ({'reason_code': ['private-owner-value']}, {'error': 'owner_request_rejected'}),
    ({'detail': 'private-owner-value'}, {'error': 'owner_request_rejected'})])
def test_launch_error_disclosure_is_an_explicit_allowlist(monkeypatch, body, expected):
    raw = json.dumps(body).encode()
    class Connection:
        def __init__(self, *args, **kwargs): pass
        def request(self, *args, **kwargs): pass
        def getresponse(self):
            return SimpleNamespace(status=409, read=lambda bound: raw[:bound])
        def close(self): pass
    monkeypatch.setattr(http.client, 'HTTPConnection', Connection)
    status, media, returned = forward(Peer(57021, 'private-peer-token'),
        Route.parse('/api/deployment/v1/campaign-launches'), 'POST', b'{}', 'test')
    assert status == 409 and media == 'application/json'
    assert json.loads(returned) == expected and b'private-owner-value' not in returned
