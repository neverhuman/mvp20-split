"""Operator config and real CLI history/readiness; no actual-peer admission claim."""
import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request,ProxyHandler,build_opener
import pytest
from amphora_agent_planning.topology.hosting import ConfiguredTopology

spec=importlib.util.spec_from_file_location('topology_host_vectors',Path(__file__).with_name('test_storage.py'))
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
pytestmark=pytest.mark.postgres


def configuration(tmp_path,profiles=()):
    body={'profiles':list(profiles),'runtime':{'endpoint':'http://127.0.0.1:12345','token_env':'TOPOLOGY_RUNTIME_TOKEN'},
        'registry':{'endpoint':'http://127.0.0.1:12346','token_env':'TOPOLOGY_REGISTRY_TOKEN'}}
    path=tmp_path/'topology.json';path.write_text(json.dumps(body),encoding='utf-8')
    return path,body,{'TOPOLOGY_RUNTIME_TOKEN':'r'*32,'TOPOLOGY_REGISTRY_TOKEN':'g'*32}


def test_configured_profiles_are_validated_and_secrets_stay_external(stored,tmp_path):
    actor,request,peer,ops=S.setup(stored)
    path,body,env=configuration(tmp_path,[{'policy':peer.state.policy().model_dump(mode='json'),'plan':peer.state.plan().model_dump(mode='json')}])
    configured=ConfiguredTopology.load(path,env)
    assert configured.resolver.profiles[0].reference==request.policy
    assert configured.operations(stored.engine).journal.engine is stored.engine
    assert configured.peers(actor.scope).scope==actor.scope
    assert env['TOPOLOGY_RUNTIME_TOKEN'] not in repr(configured)
    body['profiles'].append(body['profiles'][0]);path.write_text(json.dumps(body),encoding='utf-8')
    with pytest.raises(ValueError,match='topology_duplicate_profile'):ConfiguredTopology.load(path,env)


@pytest.mark.parametrize('mode',['extra','duplicate','missing-token','bad-endpoint','wrong-parent','oversize'])
def test_bad_config_rejects_before_hosting(stored,tmp_path,mode):
    actor,request,peer,ops=S.setup(stored);path,body,env=configuration(tmp_path)
    if mode=='extra':body['extra']='not allowed'
    elif mode=='duplicate':path.write_text('{"profiles":[],"profiles":[]}',encoding='utf-8')
    elif mode=='missing-token':env={}
    elif mode=='bad-endpoint':body['runtime']['endpoint']='http://remote.example:80'
    elif mode=='wrong-parent':
        plan=peer.state.plan().model_dump(mode='json');plan['sha256']='f'*64
        body['profiles']=[{'policy':peer.state.policy().model_dump(mode='json'),'plan':plan}]
    else:path.write_bytes(b'x'*8388609)
    if mode not in {'duplicate','oversize'}:path.write_text(json.dumps(body),encoding='utf-8')
    with pytest.raises((ValueError,KeyError)):ConfiguredTopology.load(path,env)


def test_real_cli_serves_retained_history_with_zero_active_profiles(stored,tmp_path):
    actor,request,peer,ops=S.setup(stored);original=ops.propose(actor,request)
    path,_,tokens=configuration(tmp_path)
    env=dict(os.environ,**tokens,PYTHONUTF8='1',AMPHORA_PLANNING_TOPOLOGY_CONFIG=str(path),
        AMPHORA_PLANNING_DATABASE_URL=stored.engine.url.render_as_string(hide_password=False),
        AMPHORA_PLANNING_SUPERVISION_CREDENTIALS=json.dumps([{'token':'t'*32,'actor_id':actor.actor_id,
            'scope':actor.scope.model_dump(mode='json'),'actions':['read_topology']}]))
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1',0));port=reservation.getsockname()[1]
    opener=build_opener(ProxyHandler({}));base='http://127.0.0.1:'+str(port)
    with (tmp_path/'host.log').open('wb') as log:
        process=subprocess.Popen([sys.executable,'-m','amphora_agent_planning.supervision_api','--port',str(port)],env=env,stdout=log,stderr=log)
        try:
            deadline=time.monotonic()+20
            while True:
                assert process.poll() is None,'Planning host exited; inspect owned test log'
                try:
                    with opener.open(base+'/ready',timeout=1) as response:assert json.load(response)['mode']=='supervisor_intake_and_topology'
                    break
                except URLError:
                    assert time.monotonic()<deadline,'Planning host readiness timeout'
                    time.sleep(.05)
            with opener.open(Request(base+'/v1/topology-proposals/'+request.proposal_id,headers={'Authorization':'Bearer '+'t'*32}),timeout=5) as response:
                assert json.load(response)==original.model_dump(mode='json')
        finally:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)


def test_cli_invalid_topology_configuration_does_not_echo_secrets(stored,tmp_path):
    path,body,tokens=configuration(tmp_path);body['runtime']['endpoint']='fixture-private-invalid-address';path.write_text(json.dumps(body),encoding='utf-8')
    env=dict(os.environ,**tokens,AMPHORA_PLANNING_TOPOLOGY_CONFIG=str(path),
        AMPHORA_PLANNING_DATABASE_URL=stored.engine.url.render_as_string(hide_password=False),
        AMPHORA_PLANNING_SUPERVISION_CREDENTIALS=json.dumps([{'token':'t'*32,'actor_id':'fixture','scope':stored.principal.scope.model_dump(mode='json'),'actions':['read_topology']}]))
    result=subprocess.run([sys.executable,'-m','amphora_agent_planning.supervision_api'],env=env,capture_output=True,timeout=20)
    assert result.returncode!=0 and b'Traceback' not in result.stderr
    assert b'fixture-private' not in result.stderr and tokens['TOPOLOGY_RUNTIME_TOKEN'].encode() not in result.stderr
