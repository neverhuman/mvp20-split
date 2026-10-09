import pytest

from amphora_local_gateway.configuration import GatewayError, Peer
from amphora_local_gateway.proxy import Route


@pytest.mark.parametrize('path', ['http://remote/api/runtime/v1/runs', '//remote/api/runtime/v1/runs',
    '/api/unknown/v1/runs', '/api/runtime/admin', '/api/runtime/v1/../admin',
    '/api/runtime/v1/%2e%2e/admin', '/api/runtime/v1/%252e%252e/admin', '/api/runtime/v1/a%5cb',
    '/api/runtime/v1/runs#secret', '/api/runtime/v1/a%2fb'])
def test_reject_arbitrary_or_ambiguous_route(path):
    with pytest.raises(GatewayError): Route.parse(path)


def test_alias_and_query_preserve_owner_contract():
    route = Route.parse('/api/data/v1/artifacts/abc?limit=20&cursor=x%2Fy')
    assert route.owner == 'artifact'
    assert route.target == '/v1/artifacts/abc?limit=20&cursor=x%2Fy'


@pytest.mark.parametrize('endpoint',['https://127.0.0.1:99','http://localhost:99','http://remote:99','http://secret@127.0.0.1:99','http://127.0.0.1:99/redirect'])
def test_peer_must_be_explicit_credential_free_loopback(endpoint):
    with pytest.raises(GatewayError): Peer.load({'endpoint':endpoint,'token_env':'AMPHORA_TOKEN'}, {'AMPHORA_TOKEN':'x'*40})


@pytest.mark.parametrize('path', ['/api/deployment/v1/campaign-launches',
    '/api/deployment/v1/campaign-launch-profiles', '/api/deployment/v1/campaign-launches/request%3A1'])
def test_only_explicit_campaign_launch_surface_is_routable(path):
    assert Route.parse(path).owner == 'deployment'


@pytest.mark.parametrize('path', ['/api/deployment/v1/owners/runtime/start',
    '/api/deployment/v1/status', '/api/deployment/v1/campaign-launches/a/start',
    '/api/deployment/v1/campaign-launches?project=foreign'])
def test_launch_peer_never_exposes_supervisor_or_query_authority(path):
    with pytest.raises(GatewayError): Route.parse(path)
