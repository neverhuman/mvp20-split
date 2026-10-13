"""Pinned additive Planning upgrade; shared cut requires exact isolated readback proof."""
import argparse
import hashlib
import os
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.installation import OwnerInstallation
from amphora_deployment.persistence.migrations import require_stopped
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.scientific_workers.ownership import require_released
from amphora_deployment.campaign_launch.backup import require_launches_drained
from campaign_curation_fixture.recovery import read
from local_numeric_configuration import write


def migrate(root, installation, predecessor, inventory, output, rehearsal=None):
    baseline=read(inventory/'inventory-evidence.json')
    backup_id='3771efc579754533993bb6a6affaf642'
    identity=OwnerInstallation.from_directory('planning',installation,
        Path(__file__).absolute().parents[2]/'services/agent_planning/uv.lock')
    assert identity.release=='0.138.0'
    original=Path(baseline['root'])
    if root==original:
        assert rehearsal is not None
        proof=read(rehearsal/'read-evidence.json')
        assert proof['status']=='passed' and proof['backup_id']==backup_id
        assert proof['target_deployment_id']!=LocalState.snapshot(root)['deployment_id']
        assert Path(proof['planning_installation'])==installation
        assert proof['readbacks_sha256']==baseline['readbacks_sha256']
        assert read(rehearsal/'drain.json')['status']=='drained'
    else:
        assert LocalState.snapshot(root)['restore']['backup_id']==backup_id
    assert read(predecessor/'manifest.json')['packages']['amphora-agent-planning']=='0.107.0'
    old=predecessor/'environment/Lib/site-packages/amphora_agent_planning/persistence/migrations/versions'
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in old.iterdir() if p.suffix in {'.py','.sql'}}
    assert hashes
    wheel=next((installation/'wheels').glob('amphora_agent_planning-0.138.0-*.whl'))
    with zipfile.ZipFile(wheel) as archive:
        for name,digest in hashes.items():
            assert hashlib.sha256(archive.read('amphora_agent_planning/persistence/migrations/versions/'+name)).hexdigest()==digest
    output.mkdir(parents=True,exist_ok=False)
    with LocalState(root) as state:
        assert state.record['phase']=='stores_ready'
        require_stopped(state.record['routes']);require_released(root,state.identity)
        require_launches_drained(root)
        bundle=CredentialVault(root/'credentials.dpapi',state.identity).load()
        password=bundle.environment(['PG_PLANNING_MIGRATOR_PASSWORD'])['PG_PLANNING_MIGRATOR_PASSWORD']
        pg=state.record['postgres'];assert pg['host']=='127.0.0.1'
        env={k:v for k,v in os.environ.items() if k.upper() in {
            'SYSTEMROOT','WINDIR','PATH','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','COMSPEC'}}
        env.update(PYTHONUTF8='1',AMPHORA_PLANNING_MIGRATION_URL='postgresql+psycopg://planning_migrator:'+quote(password,safe='')+'@127.0.0.1:'+str(pg['port'])+'/amphora_local?connect_timeout=5')
        evidence={'status':'running','started_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'owner':'planning','release':identity.release,'backup_id':backup_id,
            'target_deployment_id':state.identity,'shared_demo':root==original,
            'initial_receipt_preserved':state.record['migrations'].get('planning'),
            'prior_migration_hashes':hashes,'installation_manifest_sha256':identity.installation_manifest_sha256,
            'approval':'UI-01.08 approved additive curation boundary; UI-01.08j managed delivery'}
        write(output/'migration.json',evidence)
        with (output/'migration.log').open('wb') as log:
            result=subprocess.run([str(installation/'environment/Scripts/python.exe'),'-I','-m',
                'amphora_agent_planning.persistence.migrate'],env=env,stdout=log,stderr=log,
                timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
        evidence.update(status='passed' if result.returncode==0 else 'failed',exit_code=result.returncode,
            finished_local=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        write(output/'migration.json',evidence)
        assert result.returncode==0,'Planning migration failed; retain evidence for forward repair'
    print('Pinned additive Planning migration passed; public readback still required',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','installation','predecessor','inventory','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--rehearsal',type=Path)
    args=parser.parse_args()
    migrate(*(getattr(args,name).absolute() for name in ('root','installation','predecessor','inventory','output')),
        rehearsal=args.rehearsal.absolute() if args.rehearsal else None)
