"""Exact scientific campaign/provenance reads on separately restored owner stores."""
import argparse
import hashlib
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from campaign_curation_fixture.session import PublicOwners
from campaign_curation_fixture.recovery import read
from local_records_controller import RecordsController
from local_numeric_configuration import write


def verify(root, restored, inventory, deployment, output, planning=None):
    output.mkdir(parents=True,exist_ok=False)
    owners=read(restored/'owners.json')
    owners['owners'].pop('registry')  # No discovery/tool work needed for retained reads.
    if planning is not None:
        owners['owners']['planning']['installation']=str(planning)
        owners['owners']['planning']['source_lock']=str(Path(__file__).absolute().parents[2]/'services/agent_planning/uv.lock')
    write(output/'owners.json',owners)
    state=LocalState.snapshot(root)
    assert state['restore']['backup_id']=='3771efc579754533993bb6a6affaf642'
    bundle=CredentialVault(root/'credentials.dpapi',state['deployment_id']).load()
    refs=bundle.environment([name.upper()+'_OPERATOR_TOKEN' for name in owners['owners']])
    tokens={name:refs[name.upper()+'_OPERATOR_TOKEN'] for name in owners['owners']}
    controller=RecordsController(root,output,Routes.load(root),
        deployment_python=deployment/'environment/Scripts/python.exe')
    started=False
    try:
        controller.start();started=True
        api=PublicOwners(controller,tokens,1)
        expected=read(inventory/'readbacks.json')
        for identity,record in expected['runs'].items():
            assert api.call('runtime','/v3/graph-runs/'+identity)==record
        draft=read(inventory/'inventory-evidence.json')['draft']
        assert api.call('runtime','/v1/definition-drafts/'+draft['draft_id']+'?revision='+str(draft['revision']))==expected['draft']
        origin=api.call('planning','/v1/campaign-origins/'+draft['draft_id']+
            '?revision='+str(draft['revision'])+'&content_sha256='+draft['content_sha256'])
        assert origin==expected['origin']
        write(output/'read-evidence.json',{'status':'passed',
            'timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'target_deployment_id':state['deployment_id'],'backup_id':state['restore']['backup_id'],
            'planning_installation':owners['owners']['planning']['installation'],
            'readbacks_sha256':hashlib.sha256((inventory/'readbacks.json').read_bytes()).hexdigest(),
            'exact_original_runs':list(expected['runs']),'exact_draft_and_origin':True,
            'provider_calls':0,'campaigns_launched':0,'deployment_launch_history':'retained in backup, not restored as live worker ownership'})
    finally:
        try:
            if started and controller.process.poll() is None:
                write(output/'drain.json',{'status':'drained','final':controller.drain()})
        finally:controller.close()
    print('Restored original scientific campaign/draft/provenance reads passed and drained',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','restored','inventory','deployment','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--planning',type=Path)
    args=parser.parse_args()
    verify(*(getattr(args,name).absolute() for name in ('root','restored','inventory','deployment','output')),
        planning=args.planning.absolute() if args.planning else None)
