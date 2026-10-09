"""Compose public Knowledge configuration into the scientific fixture deployment."""
import json
from pathlib import Path
from local_numeric_configuration import write


def connect(output, records_directory):
    owners = json.loads((output / 'owners.json').read_bytes())
    prepared = json.loads((records_directory / 'owners.json').read_bytes())['owners']
    for name in ('research', 'knowledge'):
        owners['owners'][name] = prepared[name]
    artifact = json.loads((output / 'artifact.json').read_bytes())
    source = json.loads(Path(prepared['artifact']['configuration']).read_bytes())
    artifact['acquisition'] = True
    artifact['profiles'].extend(source['profiles'])
    for principal in artifact['principals']:
        if principal['actor_id'] == 'admin':
            principal['actions'].append('source_history')
    artifact['principals'].extend(p for p in source['principals'] if p['actor_id'] == 'knowledge')
    owners['owners']['artifact']['secret_references'].append('KNOWLEDGE_DATA_TOKEN')
    write(output / 'artifact.json', artifact)
    write(output / 'owners.json', owners)
