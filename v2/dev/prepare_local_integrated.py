"""Compose immutable scientific/model configs with exact public owner context; no model calls."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from check_boundaries import ROOT
from local_numeric_configuration import bind_workers, prepare, write
from local_records_controller import RecordsController
from verify_local_owner_records import Scenario


def compose(output, bundle, materials, source_manifest, checkpoint, records_directory):
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    original, vault = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    records = json.loads((records_directory / 'records.json').read_bytes())
    scope = records['question']['reference']['scope']
    routes = Routes.load(root)
    material, identity, ports = prepare(output, bundle, materials, source_manifest, original['deployment_id'],
        routes, project=scope['project_id'], delivery=True)
    assert material['scope'] == scope
    owners = json.loads((output / 'owners.json').read_bytes())['owners']
    checkpoint_owners = json.loads((checkpoint / 'owners.json').read_bytes())['owners']
    record_owners = json.loads((records_directory / 'owners.json').read_bytes())['owners']
    tokens = CredentialVault(root / 'credentials.dpapi', original['deployment_id']).load().environment(
        ['ARTIFACT_OPERATOR_TOKEN', 'RESEARCH_OPERATOR_TOKEN', 'KNOWLEDGE_OPERATOR_TOKEN'])
    # Read actual owners under their existing configuration. Never regenerate graph assertions here.
    controller = RecordsController(root, records_directory, routes)
    try:
        controller.start()
        scenario = Scenario(controller, tokens, scope, output)
        for owner, path, name in [('research', 'questions', 'question'), ('research', 'evidence-needs', 'need'),
                                  ('knowledge', 'graph-snapshots', 'snapshot')]:
            assert scenario.call(owner, '/v1/' + path + '/read', records[name]['reference']) == records[name]
        context = {'profile': 'synthetic-demo-context.v1', 'question': records['question']['reference'],
            'objective': records['question']['objective'], 'need': records['need']['reference'],
            'snapshot': records['snapshot']['reference'], 'assertions': [
                {'id': row['reference']['assertion_id'], 'statement': row['statement'],
                 'posture': row['posture'], 'predicate': row['predicate']}
                for row in records['snapshot']['content']['assertions']],
            'source': {'artifact_id': records['artifact']['artifact_id'], 'sha256': records['artifact']['sha256']},
            'limits': 'Synthetic structural hypothesis only; not scientific efficacy or validated biology.'}
        write(output / 'owner-context.json', context)
        write(output / 'owner-readback.json', {name: records[name] for name in ('question', 'need', 'snapshot')})
        context_body = json.dumps(context, sort_keys=True, separators=(',', ':')).encode()
        context_ref = scenario.publish(context_body, records['artifact']['schema_ref'], 'application/octet-stream')
        record_drain = controller.drain()
    finally:
        controller.close()
    # Publish the new objective through a fresh Data-only manifest with the retained profile.
    stage = output / 'publication'
    stage.mkdir()
    data = json.loads((checkpoint / 'artifact.json').read_bytes())
    publication_data = dict(data, profiles=[dict(row, schema_path=str(checkpoint / row['schema_path']))
        if 'schema_path' in row else row for row in data['profiles']])
    write(stage / 'artifact.json', publication_data)
    write(stage / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': {'artifact':
        dict(checkpoint_owners['artifact'], configuration=str(stage / 'artifact.json'))}})
    controller = RecordsController(root, stage, routes)
    try:
        controller.start()
        scenario = Scenario(controller, tokens, scope, output)
        profile = next(row for row in data['profiles'] if row['media_type'] == 'text/plain')
        schema = {key: value for key, value in profile.items() if key != 'media_type'}
        objective = scenario.publish(b'Inspect the pinned Research question and Knowledge hypothesis before the synthetic numeric seed tool. '
            b'This fixture tests software integration, not scientific truth. Retain uncertainty. If there is no justified supported change, '
            b'abstain so the bounded numeric campaign can continue unchanged. Explain how the supplied hypothesis limits conclusions.', schema, 'text/plain')
        publication_drain = controller.drain()
    finally:
        controller.close()
    recipe = json.loads((checkpoint / 'recipe.json').read_bytes())
    recipe.update(objective=objective, entries=[{'artifact': context_ref, 'role': 'knowledge', 'required': True}])
    write(output / 'recipe-input.json', recipe)
    # Preserve exact scientific schemas and add only checkpoint context profiles; no name collisions.
    data_numeric = json.loads((output / 'artifact.json').read_bytes())
    known = {(row['schema_id'], row['version'], row['sha256']) for row in data_numeric['profiles']}
    for row in data['profiles']:
        if (row['schema_id'], row['version'], row['sha256']) in known:
            continue
        row = dict(row)
        if 'schema_path' in row:
            name = 'checkpoint-' + row['schema_path']
            shutil.copyfile(checkpoint / row['schema_path'], output / name)
            row['schema_path'] = name
        data_numeric['profiles'].append(row)
    data_numeric['principals'] += [row for row in data['principals'] if row['actor_id'] in ('planning', 'knowledge')]
    for row in data_numeric['principals']:
        if row['actor_id'] == 'runtime' and 'source_history' not in row['actions']:
            row['actions'].append('source_history')
    write(output / 'artifact.json', data_numeric)
    owners['artifact']['secret_references'] += ['PLANNING_DATA_TOKEN', 'KNOWLEDGE_DATA_TOKEN']
    runtime = json.loads((output / 'runtime.json').read_bytes())
    checkpoint_runtime = json.loads((checkpoint / 'runtime.json').read_bytes())
    runtime['principals'] += [row for row in checkpoint_runtime['principals'] if row['actor_id'] == 'planning']
    runtime['supervision'] = checkpoint_runtime['supervision']
    runtime['supervision_admission'] = {'policies': ['supervision-policy.json'], 'recipes': ['recipe.json']}
    write(output / 'runtime.json', runtime)
    owners['runtime']['secret_references'] += ['PLANNING_RUNTIME_TOKEN', 'RUNTIME_PLANNING_TOKEN']
    owners['planning'] = checkpoint_owners['planning']
    owners.update({name: record_owners[name] for name in ('research', 'knowledge')})
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    native = json.loads((output / 'native.json').read_bytes())
    old_native = json.loads((checkpoint / 'native.json').read_bytes())
    worker = json.loads((checkpoint / 'runtime-checkpoint.json').read_bytes())
    worker['actor_id'] = 'admin'
    write(output / 'runtime-checkpoint.json', worker)
    native['workers']['runtime-checkpoint'] = dict(old_native['workers']['runtime-checkpoint'],
        configuration=str(output / 'runtime-checkpoint.json'))
    native['workers']['planning-checkpoint'] = old_native['workers']['planning-checkpoint']
    write(output / 'native.json', native)
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment['PYTHONUTF8'] = '1'
    script = ROOT / 'services/campaign_runtime/tests/numeric_search/export_supervision.py'
    result = subprocess.run([str(Path(owners['runtime']['installation']) / 'environment/Scripts/python.exe'),
        '-I', str(script), str(output)], env=environment, capture_output=True, timeout=45)
    (output / 'compilation.log').write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, 'Owner-local numeric supervision compiler failed'
    bind_workers(output, bundle, material, identity, ports, 'awaiting-admission', 'standby')
    assert LocalState.snapshot(root) == original and (root / 'credentials.dpapi').read_bytes() == vault
    write(output / 'prepared.json', {'scope': scope, 'objective': objective, 'context': context_ref,
        'material': material, 'ports': ports, 'identity_directory': str(identity.directory),
        'compiled': json.loads((output / 'compiled.json').read_bytes()),
        'record_drain': record_drain, 'publication_drain': publication_drain, 'provider_calls': 0,
        'limits': ['Preparation only; required model packet fit, live execution and browser trace remain unverified']})
    print('Actual owner context pinned; numeric invoke checkpoint compiled; zero model calls', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'bundle', 'materials', 'source-manifest', 'checkpoint', 'records-directory'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    compose(*(getattr(args, name).absolute() for name in ('output', 'bundle', 'materials', 'source_manifest', 'checkpoint', 'records_directory')))
