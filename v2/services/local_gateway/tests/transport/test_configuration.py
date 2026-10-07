import json

import pytest

from amphora_local_gateway.configuration import Configuration, GatewayError


def test_configuration_carries_only_explicit_loopback_peer_and_safe_repr(tmp_path):
    record={'profile':'local-gateway-v1','public_directory':str(tmp_path),
        'peers':{'runtime':{'endpoint':'http://127.0.0.1:18000','token_env':'AMPHORA_RUNTIME_TOKEN'}},
        'context':{'actor_id':'operator','scope':{'tenant_id':'demo','project_id':'demo'},'run_id':None,'synthetic':True},
        'launcher_key_env':'AMPHORA_GATEWAY_SESSION_KEY'}
    path=tmp_path/'config.json';path.write_text(json.dumps(record))
    environment={'AMPHORA_RUNTIME_TOKEN':'runtime-private-credential-1234567890','AMPHORA_GATEWAY_SESSION_KEY':'gateway-private-credential-1234567890'}
    config=Configuration.load(path,environment)
    assert config.peers['runtime'].port==18000
    assert all(value not in repr(config) for value in environment.values())
    with pytest.raises(GatewayError):Configuration.load(path,{})
    record['context']['unexpected']='scope-change';path.write_text(json.dumps(record))
    with pytest.raises(GatewayError):Configuration.load(path,environment)
    path.write_text('{"profile":"x","profile":"y"}')
    with pytest.raises(GatewayError,match='duplicate'):Configuration.load(path,environment)
    path.write_bytes(b' '*65537)
    with pytest.raises(GatewayError,match='size'):Configuration.load(path,environment)
