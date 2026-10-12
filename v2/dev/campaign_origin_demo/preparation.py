"""Immutable successor configuration; original demo records/assets remain unchanged."""
import json
import shutil
from pathlib import Path


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return path


def prepare(source, output, installation, studio, routes):
    output.mkdir(parents=True, exist_ok=False)
    def relocate(value):
        if isinstance(value, dict):
            return {key: relocate(item) for key, item in value.items()}
        if isinstance(value, list):
            return [relocate(item) for item in value]
        if isinstance(value, str) and value.startswith(str(source) + '\\'):
            return str(output) + value[len(str(source)):]
        return value
    for path in source.glob('*.json'):
        if path.name in {'ready.json', 'drain.json', 'public-final.json', 'draft-save-receipt.json', 'draft-record.json'}:
            continue
        if path.name in {'owners.json', 'runtime.json', 'artifact.json', 'registry.json', 'gateway.json',
                         'native.json', 'launch.json', 'launch-prepared.json', 'access.json'}:
            write(output / path.name, relocate(json.loads(path.read_bytes())))
        else:
            # Published schema/descriptor bytes are hash-pinned, not editable configuration.
            shutil.copyfile(path, output / path.name)
    assets = output / 'public'
    assets.mkdir()
    for name in ('index.html', 'app.js', 'app.css'):
        shutil.copyfile(studio / name, assets / name)
    owners = json.loads((output / 'owners.json').read_bytes())['owners']
    scope = json.loads((output / 'launch-prepared.json').read_bytes())['scope']
    owner_dir = installation / 'planning'
    owners['planning'] = {'installation': str(owner_dir),
        'source_lock': str(Path(__file__).parents[2] / 'services/agent_planning/uv.lock'),
        'configuration': str(write(output / 'planning.json', {'principals': [
            {'token_env': 'AMPHORA_PLANNING_OPERATOR_TOKEN', 'actor_id': 'operator', 'scope': scope,
             'actions': ['read_campaign_origin']}]})), 'secret_references': ['PLANNING_OPERATOR_TOKEN']}
    owners['gateway']['installation'] = str(installation / 'gateway')
    owners['gateway']['source_lock'] = str(Path(__file__).parents[2] / 'services/local_gateway/uv.lock')
    owners['gateway']['secret_references'].append('PLANNING_OPERATOR_TOKEN')
    gateway = json.loads((output / 'gateway.json').read_bytes())
    gateway['public_directory'] = str(assets)
    gateway['peers']['planning'] = {'endpoint': routes.endpoint('planning'), 'token_env': 'AMPHORA_PLANNING_OPERATOR_TOKEN'}
    write(output / 'gateway.json', gateway)
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    # Source processing and declaration publication use already supported public APIs.
    artifact = json.loads((output / 'artifact.json').read_bytes())
    artifact['acquisition'] = True
    for principal in artifact['principals']:
        if principal['token_env'] == 'AMPHORA_ARTIFACT_OPERATOR_TOKEN':
            principal['actions'] = sorted(set(principal['actions']) | {'read', 'upload', 'finalize', 'acquire', 'source_history', 'manage_source_rights'})
    assert any(profile['media_type'] == 'text/plain' for profile in artifact['profiles'])
    write(output / 'artifact.json', artifact)
    write(output / 'origin-prepared.json', {'scope': scope, 'source': str(source),
        'installation': str(installation), 'status': 'prepared', 'paid_provider_calls': 0})
    return output
