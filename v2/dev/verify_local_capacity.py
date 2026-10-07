"""Installed Data owner: bounded native storage quota, replay and loopback isolation."""

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import time
import urllib.error
import urllib.request
import uuid

from amphora_deployment.lifecycle import LifecycleEvents
from amphora_deployment.lifecycle.configuration import load_bindings
from amphora_deployment.lifecycle.routes import Routes
from compose_local_readonly import compose


def verify(output):
    output.mkdir(parents=True,exist_ok=False)
    root=Path(os.environ['LOCALAPPDATA'])/'Amphora/local-v2/installation'
    identity=uuid.uuid4().hex
    config_root=root/'configurations'/('capacity-'+identity)
    manifest=compose(config_root)
    path=config_root/'artifact.json'
    config=json.loads(path.read_bytes())
    scope={'tenant_id':'internal','project_id':'capacity-'+identity}
    config['principals'][0].update(scope=scope,actions=['upload','finalize','read'])
    schema_hash=hashlib.sha256(b'{"type":"string","contentEncoding":"base64"}').hexdigest()
    config['profiles']=[{'media_type':'application/octet-stream','schema_id':'fixture.bytes','version':'1','sha256':schema_hash}]
    config['limits']={'max_bytes':8,'scope_bytes':8,'streams':1,'uploads':4,'attempts':1,'seconds':20}
    storage=root.parent/'capacity-evidence'/identity
    storage.mkdir(parents=True,exist_ok=False)
    config['storage_root']=str(storage)
    path.write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    routes=Routes.load(root)
    binding=load_bindings(root,manifest,routes)['artifact']
    token=binding.environment['AMPHORA_ARTIFACT_OPERATOR_TOKEN']
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(path,method='GET',body=None,authorization=token):
        headers={'Authorization':'Bearer '+authorization}
        raw=body if isinstance(body,bytes) else json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request(routes.endpoint('artifact')+path,method=method,data=raw,headers=headers)
        try: response=opener.open(req,timeout=5)
        except urllib.error.HTTPError as error: response=error
        with response: return response.status,response.read(65536)
    def command(family,payload):
        return {'identity':{'scope':scope,'actor_id':'operator','command_id':uuid.uuid4().hex,
                            'command_family':family},'payload':payload}
    payload=b'bounded!'
    content={'sha256':hashlib.sha256(payload).hexdigest(),'size_bytes':len(payload),'media_type':'application/octet-stream',
             'schema_ref':{'schema_id':'fixture.bytes','version':'1','sha256':schema_hash}}
    result={'checked_at':datetime.now().astimezone().isoformat(timespec='seconds'),'scope':scope,
            'installation_manifest_sha256':binding.installation.installation_manifest_sha256,
            'limits':'Eight-byte service-enforced quota on actual local storage; not physical disk exhaustion or power-loss certification.'}
    with binding.launch(LifecycleEvents(output/'logs')) as process:
        deadline=time.monotonic()+60
        while True:
            try:
                if request('/ready')[0]==200: break
            except OSError: pass
            assert process.process.poll() is None and time.monotonic()<deadline,'Data startup failed'
            time.sleep(.1)
        begin=command('artifacts.begin_upload',{'content':content})
        status,raw=request('/v1/uploads','POST',begin)
        assert status==200
        uploaded=json.loads(raw)
        upload_id=uploaded['upload_id']
        assert request('/v1/uploads/'+upload_id+'/content','PUT',payload)[0]==200
        finalize=command('artifacts.finalize',{'upload_id':upload_id,'content':content})
        accepted=request('/v1/artifacts/finalize','POST',finalize)
        assert accepted[0]==200
        artifact=json.loads(accepted[1])['artifact']
        extra=command('artifacts.begin_upload',{'content':{**content,'size_bytes':1,'sha256':hashlib.sha256(b'x').hexdigest()}})
        exhausted=request('/v1/uploads','POST',extra)
        assert exhausted[0]==409 and json.loads(exhausted[1])['reason_code']=='capacity_exhausted', 'Quota must reject new reservation'
        assert request('/v1/artifacts/finalize','POST',finalize)==accepted
        content_path='/v1/artifacts/'+artifact['artifact_id']+'/content'
        assert request(content_path)==(200,payload)
        assert request(content_path,authorization='invalid')[0]==401
        addresses={row[4][0] for row in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET,socket.SOCK_STREAM)
                   if not row[4][0].startswith('127.') and row[4][0]!='0.0.0.0'}
        assert addresses,'No non-loopback address available for selected-host isolation proof'
        for address in addresses:
            with socket.socket() as probe:
                probe.settimeout(.5)
                assert probe.connect_ex((address,binding.port))!=0,'Owner unexpectedly reachable off loopback'
        result.update(status='passed',artifact=artifact,quota_rejection=json.loads(exhausted[1]),
                      original_receipt_replayed=True,original_bytes_preserved=True,
                      non_loopback_denials=len(addresses),invalid_token_status=401)
        process.drain()
        assert process.process.wait(timeout=45)==0
        assert process.status()['drain']=='drained'
    (output/'evidence.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Installed Data quota/replay/byte preservation/network/auth/drain passed:',output,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try: verify(args.output)
    except Exception: raise SystemExit('Local capacity proof failed; raw diagnostics suppressed.') from None
