"""Extract reviewed synthetic graph materials from exact local Linux tool images."""

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

from check_boundaries import ROOT

IMAGES = {'numeric': 'sha256:7538bece7dceb2f6c395890abbc632fe58e188ba5120ef2d6ef070267809e878',
          'evaluate': 'sha256:b6d73b31058d358a5a2a13e44979e8b6e3a6acd06260670226a1b2570f1135e3'}


def prepare(output, scope, registry_python):
    output.mkdir(parents=True, exist_ok=False)

    def write(name, value):
        (output / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

    def cli(stage, action, *arguments):
        image = IMAGES['evaluate' if stage == 'evaluate' else 'numeric']
        command = ['docker', 'run', '--rm', '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', image, action]
        if stage != 'evaluate':
            command.extend(['--operation', stage])
        result = subprocess.run([*command, *arguments], capture_output=True, timeout=30)
        assert result.returncode == 0 and len(result.stdout) <= 262144, 'Actual numeric image extraction failed'
        return result.stdout

    def wire(value):
        result = subprocess.run([str(registry_python), '-I', str(ROOT / 'dev/catalog_contract_probe.py')],
            input=json.dumps(value).encode(), capture_output=True, timeout=15)
        assert result.returncode == 0, 'Installed public release validation failed'
        return json.loads(result.stdout)

    releases, locks, schemas, profiles, materials = {}, {}, {}, [], []
    for stage in ('seed', 'requests', 'collect', 'vary', 'evaluate'):
        image = IMAGES['evaluate' if stage == 'evaluate' else 'numeric']
        descriptor = json.loads(cli(stage, 'describe', '--image-sha256', image[7:]))
        assert descriptor['tool']['binding']['image_sha256'] == image[7:]
        releases[stage] = descriptor
        locks[stage] = wire({'operation': 'lock', 'descriptor': descriptor})
        name = stage + '-descriptor.json'
        write(name, descriptor)
        materials.append({'descriptor': name, 'lock': locks[stage]})
        for direction in (('input', 'output', 'policy') if stage == 'evaluate' else ('input', 'output')):
            body = cli(stage, 'schema', '--kind' if stage == 'evaluate' else '--direction', direction)
            ports = descriptor['tool']['outputs' if direction == 'output' else 'inputs']
            port = next(port for port in ports if (port['name'] == 'policy') == (direction == 'policy'))
            reference = port['schema_ref']
            assert hashlib.sha256(body).hexdigest() == reference['sha256']
            key = json.dumps(reference, sort_keys=True)
            if key in schemas:
                assert (output / schemas[key]['path']).read_bytes() == body
                continue
            name = stage + '-' + direction + '.json'
            (output / name).write_bytes(body)
            schemas[key] = {'schema_ref': reference, 'path': name}
            profiles.append({**reference, 'media_type': 'application/json', 'schema_path': name})
    # Reuse only the existing public authored fixture generator, never Runtime implementations.
    source = ROOT / 'services/campaign_runtime/tests/numeric_search/definition.py'
    spec = importlib.util.spec_from_file_location('local_numeric_definition', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    write('graph.json', module.campaign(scope, releases, 2))
    (output / 'policy.json').write_bytes(cli('evaluate', 'policy'))
    result = {'profile': 'local-numeric-demo-materials-v1', 'scope': scope, 'images': IMAGES,
        'graph': {'definition': 'graph.json', 'releases': materials, 'schemas': list(schemas.values())},
        'profiles': profiles, 'locks': locks, 'definition_generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'limits': ['Synthetic numeric fixture only; no graph admission, readiness or scientific claim'], 'provider_calls': 0}
    write('manifest.json', result)
    print('Exact Linux numeric demo descriptors, schemas and authored graph extracted', flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--project', required=True)
    parser.add_argument('--registry-python', required=True, type=Path)
    args = parser.parse_args()
    prepare(args.output.absolute(), {'tenant_id': 'internal', 'project_id': args.project}, args.registry_python.absolute())
