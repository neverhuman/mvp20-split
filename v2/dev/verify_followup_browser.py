"""Observe retained follow-up owners in production Studio; no provider or graph writes."""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

from campaign_context_fixture.support import environment
from check_boundaries import ROOT
from followup_acceptance.session import Session
from followup_acceptance.materials import run_owner, write


def output_value(session, run, expected):
    base='/v1/graph-observations/'+run+'/nodes'
    snapshot=session.runtime.call('GET',base+'?limit=50')
    node=next(item for item in snapshot['nodes'] if item['path']['node_id']=='pack')
    detail=session.runtime.call('GET',base+'/'+node['activation_id']+'?'+urlencode({'snapshot_token':snapshot['snapshot']['snapshot_token'],'limit':50}))
    artifact=next(item['artifact'] for item in detail['outputs'] if item['port']=='result')
    assert artifact['scope']==session.scope and artifact['size_bytes']<=65536
    assert session.data.call('GET','/v1/artifacts/'+artifact['artifact_id'])==artifact
    request=Request(session.data.endpoint+'/v1/artifacts/'+artifact['artifact_id']+'/content',headers={'Authorization':'Bearer '+session.data.token})
    with build_opener(ProxyHandler({})).open(request,timeout=10) as response:
        raw=response.read(65537)
    assert len(raw)==artifact['size_bytes'] and hashlib.sha256(raw).hexdigest()==artifact['sha256']
    assert json.loads(raw)=={'a':expected}
    return {'run':run,'artifact':artifact,'value':expected}


def verify(installation, records, source, output):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1'
    output=output.absolute(); output.mkdir(parents=True, exist_ok=False)
    source=source.absolute()
    session=Session.retained(installation.absolute(), records.absolute(), source)
    try:
        original=json.loads((source / 'original-run.json').read_bytes())
        assert session.runtime.call('GET','/v3/graph-runs/'+original['run_id']) == original
        successor=json.loads((source/'successor-readback.json').read_bytes())
        write(output/'output-proof.json',{'original':output_value(session,original['run_id'],1),
            'successor':output_value(session,successor['result']['run_id'],2),
            'limits':['Exact synthetic bytes changed; this does not establish scientific improvement']})
        delivery=json.loads(run_owner(session.pythons['runtime'],[ROOT/'services/campaign_runtime/tests/supervision_followup/delivery_readback.py',
            original['run_id'],successor['result']['run_id']],output,session.envs['runtime']))
        write(output/'delivery-proof.json',delivery)
        payload={'binding':{'run':original['run_id'],'scope':session.scope},'output':str(output),
            'owners':{name:{'endpoint':owner.endpoint,'token':owner.token} for name,owner in
                      [('runtime',session.runtime),('data',session.data),('research',session.research)]}}
        result=subprocess.run(['node','tests/integration/followup_live.mjs'],cwd=ROOT/'studio',env=environment(),
            input=json.dumps(payload).encode(),capture_output=True,timeout=180,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        (output/'browser.log').write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,'Actual follow-up browser failed; inspect bounded browser log'
        assert session.runtime.call('GET','/v3/graph-runs/'+original['run_id']) == original
        print('Actual follow-up browser passed; original unchanged and no new model calls',flush=True)
    finally:
        session.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['installation','records','source','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();verify(args.installation,args.records,args.source,args.output)
