"""Preserve current demo readbacks before any migration or serving configuration change."""
import argparse
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

from campaign_curation_fixture.session import session
from campaign_curation_fixture.recovery import read
from local_numeric_configuration import write


def verify(root, serving, browser, context, output):
    output.mkdir(parents=True,exist_ok=False)
    for name in ('owners.json','access.json','native.json','launch.json','launch-prepared.json'):
        shutil.copyfile(serving/name,output/name)
    owners=read(output/'owners.json')['owners']
    identities={name: {'installation':row['installation'],
        'manifest_sha256':hashlib.sha256((Path(row['installation'])/'manifest.json').read_bytes()).hexdigest(),
        'configuration_sha256':hashlib.sha256(Path(row['configuration']).read_bytes()).hexdigest(),
        'packages':read(Path(row['installation'])/'manifest.json')['packages']}
        for name,row in owners.items()}
    prepared=read(serving/'launch-prepared.json')
    expected=read(serving/'compiler-completed.json')
    prior=read(browser/'evidence.json')
    launch_ids=sorted({row['identity']['command_id'] for row in prior['receipts']})
    with session(root,output) as api:
        launches=[api.call('deployment','/v1/campaign-launches/'+identity) for identity in launch_ids]
        run_ids=sorted({prepared['baseline_run']} | {row['run_id'] for row in launches if row['run_id']})
        runs={identity:api.call('runtime','/v3/graph-runs/'+identity) for identity in run_ids}
        assert all(row['status']=='completed' for row in runs.values())
        draft=expected['draft']
        origin=api.call('planning','/v1/campaign-origins/'+draft['draft_id']+
            '?revision='+str(draft['revision'])+'&content_sha256='+draft['content_sha256'])
        assert origin['origin_sha256']==expected['origin_sha256']
        saved=api.call('runtime','/v1/definition-drafts/'+draft['draft_id']+'?revision='+str(draft['revision']))
        campaign_context=read(context)
        write(output/'campaign-context.json',campaign_context)
        write(output/'readbacks.json',{'runs':runs,'launches':launches,'origin':origin,'draft':saved})
    drained=read(output/'drain.json')
    assert drained['status']=='drained'
    write(output/'inventory-evidence.json',{'status':'passed',
        'timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'scope':prepared['scope'],'source':str(serving),'root':str(root),
        'owners':identities,'run_ids':run_ids,'draft':draft,
        'origin_sha256':origin['origin_sha256'],'readbacks_sha256':hashlib.sha256((output/'readbacks.json').read_bytes()).hexdigest(),
        'campaign_context_sha256':hashlib.sha256(context.read_bytes()).hexdigest(),
        'provider_calls':0,'campaigns_launched':0,'all_owned_processes_drained':True})
    print('Existing scientific demo inventory/readbacks passed and drained; no migration/provider/campaign',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','serving','browser','context','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    verify(*(getattr(args,name).absolute() for name in ('root','serving','browser','context','output')))
