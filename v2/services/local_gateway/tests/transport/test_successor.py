import pytest
from amphora_local_gateway.configuration import GatewayError
from amphora_local_gateway.launch_routes import LaunchRoute
from amphora_local_gateway.proxy import Route


@pytest.mark.parametrize('tail,method',[('', 'POST'),('/original','GET'),('/receipts/query','POST')])
def test_only_approved_successor_method_pairs(tail,method):
    route=Route.parse('/api/deployment/v1/campaign-successor-launches'+tail)
    policy=LaunchRoute.parse(route.target)
    policy.check(method,b'{}' if method=='POST' else b'')
    with pytest.raises(GatewayError): policy.check('GET' if method=='POST' else 'POST',b'')
    with pytest.raises(GatewayError): policy.check(method,b'x'*262145)
    if method=='GET':
        with pytest.raises(GatewayError): policy.check(method,b'{}')


@pytest.mark.parametrize('tail',['?scope=other','/receipts/query/extra','-unsafe','/id/other','/%2e%2e','/id%2fother'])
def test_successor_lookalikes_and_unapproved_paths_reject(tail):
    with pytest.raises(GatewayError): Route.parse('/api/deployment/v1/campaign-successor-launches'+tail)
