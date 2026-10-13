"""Actual installed scoped readers: original data, write denial and credential isolation."""
import argparse
import copy
import hashlib
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from amphora_deployment.curation_access import curation_credentials
from amphora_deployment.persistence.state import LocalState
from campaign_curation_fixture.session import session, PublicOwners
from campaign_curation_fixture.recovery import read, retained
from local_numeric_configuration import write


def verify(root, serving, deployment, records, output):
    output.mkdir(parents=True, exist_ok=False)
    assert read(deployment / 'manifest.json')['packages']['amphora-deployment'] == '0.20.1'
    original_hash = hashlib.sha256((root / 'credentials.dpapi').read_bytes()).hexdigest()
    python = deployment / 'environment/Scripts/python.exe'
    code = ('from amphora_deployment.curation_access import provision_curation_credentials; '
            'import sys; provision_curation_credentials(sys.argv[1])')
    subprocess.run([str(python), '-I', '-c', code, str(root)], check=True, timeout=30,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    for name in ('owners.json','access.json','native.json','launch.json','launch-prepared.json'):
        shutil.copyfile(serving / name, output / name)
    prepared = read(output / 'launch-prepared.json')
    prepared['deployment_python'] = str(python)
    write(output / 'launch-prepared.json', prepared)
    owners = read(output / 'owners.json')
    scope = read(serving / 'integrated-evidence.json')['scope']
    for name, action in [('knowledge','read_graph'),('research','read_declarations')]:
        reference = 'PLANNING_' + name.upper() + '_TOKEN'
        config = read(Path(owners['owners'][name]['configuration']))
        config['principals'].append({'token_env': 'AMPHORA_' + reference,
            'actor_id': 'planning-reader', 'scope': scope, 'actions': [action]})
        owners['owners'][name]['configuration'] = str(write(output / (name + '.json'), config))
        for owner in (name, 'planning'):
            owners['owners'][owner]['secret_references'].append(reference)
    write(output / 'owners.json', owners)
    bundle = curation_credentials(root, LocalState.snapshot(root)['deployment_id'])
    values = bundle.environment(bundle.names)
    questions = read(records / 'questions.json')
    revision = read(records / 'decision.json')['decision']['head']['snapshot']
    assert questions['reference']['scope'] == revision['graph']['scope'] == scope
    with session(root, output) as api:
        retained(api, serving, read(serving / 'integrated-evidence.json'))
        peer = PublicOwners(api.controller, {
            'knowledge': values['PLANNING_KNOWLEDGE_TOKEN'],
            'research': values['PLANNING_RESEARCH_TOKEN']}, prepared['launch_port'])
        snapshot = peer.call('knowledge','/v1/graph-snapshots/read',revision)
        assert snapshot == api.call('knowledge','/v1/graph-snapshots/read',revision)
        assert peer.call('research','/v1/questions/read',questions['reference']) == questions
        peer.call('knowledge','/v1/graph-rebuilds',{'wire_version':'1',
            'graph':revision['graph'],'rebuild_id':'reader-must-not-rebuild'},allowed=(403,))
        peer.call('research','/v1/questions',questions,allowed=(403,))
        foreign = copy.deepcopy(revision)
        foreign['graph']['scope']['project_id'] = 'outside-reader-scope'
        peer.call('knowledge','/v1/graph-snapshots/read',foreign,allowed=(403,))
        foreign = copy.deepcopy(questions['reference'])
        foreign['scope']['project_id'] = 'outside-reader-scope'
        peer.call('research','/v1/questions/read',foreign,allowed=(403,))
        peer.tokens['knowledge'],peer.tokens['research'] = peer.tokens['research'],peer.tokens['knowledge']
        peer.call('knowledge','/v1/graph-snapshots/read',revision,allowed=(401,))
        peer.call('research','/v1/questions/read',questions['reference'],allowed=(401,))
        retained(api, serving, read(serving / 'integrated-evidence.json'))
        assert hashlib.sha256((root / 'credentials.dpapi').read_bytes()).hexdigest() == original_hash
        write(output / 'peer-evidence.json', {'status':'passed',
            'timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'deployment_release':'0.20.1','scope':scope,'snapshot':revision,
            'question':questions['reference'],'original_vault_unchanged':True,
            'same_scope_reads':'exact originals','peer_writes':'403','foreign_scope':'403',
            'swapped_credentials':'401','provider_calls':0,'new_campaigns':0})
    print('Installed scoped peer reads/denials passed; original receipts retained and drained',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root','serving','deployment','records','output'):
        parser.add_argument('--' + name,type=Path,required=True)
    args=parser.parse_args()
    verify(*(getattr(args,name).absolute() for name in ('root','serving','deployment','records','output')))
