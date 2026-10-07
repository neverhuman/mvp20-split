"""Add the existing Data text schema to a fresh reviewed Runtime configuration."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from local_numeric_configuration import write


def prepare(source, correction, output):
    output.mkdir(parents=True, exist_ok=False)
    for path in source.glob('*.json'):
        shutil.copyfile(path, output / path.name)
    evidence = json.loads((correction / 'correction-evidence.json').read_bytes())
    assert evidence['status'] == 'passed'
    schema = evidence['artifact']['schema_ref']
    content = b'{"type":"string"}'
    assert schema['sha256'] == hashlib.sha256(content).hexdigest()
    schema_path = output / 'reviewed-text-schema.json'
    schema_path.write_bytes(content)
    owners = json.loads((source / 'owners.json').read_bytes())['owners']
    original_path = Path(owners['runtime']['configuration'])
    runtime = json.loads(original_path.read_bytes())
    for graph in runtime['graphs']:
        graph['definition'] = str((original_path.parent / graph['definition']).absolute())
        for release in graph['releases']:
            release['descriptor'] = str((original_path.parent / release['descriptor']).absolute())
        for row in graph['schemas']:
            row['path'] = str((original_path.parent / row['path']).absolute())
        if not any(row['schema_ref'] == schema for row in graph['schemas']):
            graph['schemas'].append({'schema_ref': schema, 'path': str(schema_path)})
    for field in ('policies', 'recipes'):
        runtime['supervision_admission'][field] = [str((original_path.parent / name).absolute())
            for name in runtime['supervision_admission'][field]]
    owners['runtime']['configuration'] = str(write(output / 'reviewed-runtime.json', runtime))
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    print('Fresh Runtime configuration pins the exact existing text schema; original journal preserved')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'correction', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    prepare(*(getattr(args, name).absolute() for name in ('source', 'correction', 'output')))
