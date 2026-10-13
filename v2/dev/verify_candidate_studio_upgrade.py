"""Freeze new Studio assets and inspect the original managed demo without new work."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.persistence.state import LocalState
from campaign_curation_fixture.session import session
from campaign_curation_fixture.verify import filtered_environment
from curation_managed_demo.serving_copy import copy_serving
from curation_managed_demo.static_identity import verify_static
from curation_live_qualification.run import credential

ROOT=Path(__file__).absolute().parents[1]


def verify(args):
    root,source,serving,public,output,tls=[getattr(args,key).absolute() for key in ('root','source','serving','public','output','tls')]
    output.mkdir(parents=True,exist_ok=False)
    changes=copy_serving(source,serving)
    for name in ('index.html','app.js','app.css'):
        shutil.copyfile(public/name,serving/'public'/name)
    hashes={name:hashlib.sha256((serving/'public'/name).read_bytes()).hexdigest() for name in ('index.html','app.js','app.css')}
    state=LocalState.snapshot(root)
    key=CredentialVault(root/'credentials.dpapi',state['deployment_id']).load().environment(['GATEWAY_SESSION_KEY'])['GATEWAY_SESSION_KEY']
    environment=filtered_environment();environment['AMPHORA_BROWSER_LAUNCH_KEY']=key
    environment['NODE_EXTRA_CA_CERTS']=str(tls/'amphora-demo-ca.pem')
    records=[]
    # The existing live recipe validates credential presence even when its worker
    # remains unstarted. Preserve that guard; never start curation in this review.
    with session(root,serving,model_key=credential(Path('Z:/ssos/.env'))) as api:
        verify_static(api,serving,output)
        for label in ('local','lan'):
            original=ROOT/'.test-results'/('curation-demo-successor-review-20261013d' if label=='local' else 'curation-demo-lan-successor-20261013d')/'input.json'
            value=json.loads(original.read_bytes())
            assert value['review_only'] is True
            value['expected_assets']=hashes;value['expect_no_structure']=True
            request=output/(label+'-input.json');request.write_text(json.dumps(value),encoding='utf-8')
            record=api.call('planning','/v1/campaign-curations/'+value['curation_id'])
            assert record['receipt']['phase']=='ready'
            lan=None
            if label=='lan':
                lan_folder=output/'lan-session'
                manifest=json.loads((serving/'owners.json').read_bytes())
                interpreter=Path(manifest['owners']['gateway']['installation'])/'environment/Scripts/python.exe'
                log=(output/'lan.log').open('wb')
                lan=subprocess.Popen([sys.executable,'-X','utf8',str(ROOT/'dev/serve_lan_review.py'),'serve',
                    '--root',str(root),'--session',str(lan_folder),'--baseline',str(serving/'gateway.json'),
                    '--tls',str(tls),'--python',str(interpreter),'--duration','240'],cwd=ROOT/'dev',
                    env=filtered_environment(),stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                if lan:
                    for _ in range(120):
                        if lan.poll() is not None:raise RuntimeError('upgrade_lan_exited')
                        if (lan_folder/'ready.json').exists():break
                        time.sleep(.25)
                    else:raise RuntimeError('upgrade_lan_start_timeout')
                with (output/(label+'-browser.log')).open('wb') as log_browser:
                    result=subprocess.run(['node','tests/integration/curation_scientific_successor.mjs',str(request),str(output/label)],
                        cwd=ROOT/'studio',env=environment,stdout=log_browser,stderr=subprocess.STDOUT,timeout=240,
                        creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode:raise RuntimeError('upgrade_'+label+'_browser_failed')
                assert api.call('planning','/v1/campaign-curations/'+value['curation_id'])==record
                records.append(label)
            finally:
                if lan:
                    (lan_folder/'STOP').touch()
                    try:lan.wait(timeout=45)
                    except subprocess.TimeoutExpired:lan.terminate();lan.wait(timeout=10)
                    log.close()
    evidence={'status':'passed','timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'serving':str(serving),'assets':hashes,'surfaces':records,'rewritten_paths':len(changes),
        'new_campaigns':0,'provider_calls':0,'original_planning_records':'unchanged',
        'limits':['Original scalar campaigns correctly have no chemical structure','LAN check originates on this host; prior LAN-01 remote firewall acceptance unchanged']}
    (output/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print('Candidate Studio upgrade passed and drained: '+str(output),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('root','source','serving','public','output','tls'):parser.add_argument('--'+key,type=Path,required=True)
    verify(parser.parse_args())
