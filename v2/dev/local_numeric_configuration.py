"""Immutable local demo composition; public owner configuration, no SQL or admission."""

import json
import shutil
import socket
from contextlib import ExitStack
from pathlib import Path

from amphora_deployment.scientific_workers.profiles import ToolProfile
from amphora_deployment.tool_access import TLSIdentity


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return path


def prepare(output, bundle, materials, source_manifest, installation_id, routes, *, project=None, delivery=False):
    output.mkdir(parents=True, exist_ok=False)
    bundle.mkdir(parents=True, exist_ok=False)
    material = json.loads((materials / 'manifest.json').read_bytes())
    for path in materials.glob('*.json'):
        if path.name != 'manifest.json':
            shutil.copyfile(path, output / path.name)
    scope = material['scope']
    if project is not None:
        scope['project_id'] = project
        graph = json.loads((output / 'graph.json').read_bytes())
        graph['scope'] = scope
        write(output / 'graph.json', graph)
    source = json.loads(source_manifest.read_bytes())
    owners = {name: dict(source['owners'][name]) for name in ('runtime', 'artifact', 'registry')}

    def principal(actor, token, actions):
        return {'actor_id': actor, 'scope': scope, 'token_env': 'AMPHORA_' + token, 'actions': actions}

    runtime = {'database_url_env': 'AMPHORA_RUNTIME_DATABASE_URL', 'fixtures': [], 'graphs': [material['graph']],
        'tools': [json.loads((output / entry['descriptor']).read_bytes())['tool'] for entry in material['graph']['releases']],
        'principals': [principal('admin', 'RUNTIME_OPERATOR_TOKEN', ['admit', 'cancel', 'read', 'inspect_receipts', 'deliver', 'maintain']),
            principal('science-slot', 'WORKER_RUNTIME_TOKEN', ['claim', 'renew', 'complete', 'read']),
            principal('artifact', 'ARTIFACT_RUNTIME_TOKEN', ['outcome'])],
        'artifacts': {'runtime_owner': 'runtime', 'reserve_endpoint': routes.endpoint('artifact') + '/v1/reservations',
                      'token_env': 'AMPHORA_RUNTIME_ARTIFACT_TOKEN'},
        'bindings': {'endpoint': routes.endpoint('artifact'), 'token_env': 'AMPHORA_RUNTIME_ARTIFACT_TOKEN'},
        'projections': {'endpoint': routes.endpoint('artifact'), 'token_env': 'AMPHORA_RUNTIME_ARTIFACT_TOKEN'},
        'inspection': {'cursor_key_env': 'AMPHORA_CURSOR_KEY'}}
    previous_data = json.loads(Path(owners['artifact']['configuration']).read_bytes())
    artifact = {'database_url_env': 'AMPHORA_ARTIFACT_DATABASE_URL', 'storage_root': previous_data['storage_root'],
        'profiles': material['profiles'], 'principals': [
            principal('admin', 'ARTIFACT_OPERATOR_TOKEN', ['upload', 'finalize', 'read']),
            principal('science-slot', 'WORKER_ARTIFACT_TOKEN', ['upload', 'finalize', 'read']),
            principal('runtime', 'RUNTIME_ARTIFACT_TOKEN', ['upload', 'finalize', 'read', 'retention'])],
        'runtime': {'owner': 'runtime', 'endpoint': routes.endpoint('runtime') + '/v1/completion-intents/outcome',
                    'token_env': 'AMPHORA_ARTIFACT_RUNTIME_TOKEN'}}
    registry = {'database_url_env': 'AMPHORA_REGISTRY_DATABASE_URL', 'principals': [
        principal('admin', 'REGISTRY_OPERATOR_TOKEN', ['register', 'activate', 'deploy', 'read', 'resolve']),
        principal('science-slot', 'WORKER_REGISTRY_TOKEN', ['heartbeat'])],
        'resources': {'architecture': 'x86_64', 'operating_system': 'linux', 'cpu_millicores': 10000,
            'memory_mib': 5120, 'gpu_count': 0, 'timeout_seconds': 60, 'max_parallel_invocations': 5, 'max_batch_size': 128}}
    references = {'runtime': ['RUNTIME_OPERATOR_TOKEN', 'WORKER_RUNTIME_TOKEN', 'ARTIFACT_RUNTIME_TOKEN',
                              'RUNTIME_ARTIFACT_TOKEN', 'CURSOR_KEY'],
        'artifact': ['ARTIFACT_OPERATOR_TOKEN', 'WORKER_ARTIFACT_TOKEN', 'RUNTIME_ARTIFACT_TOKEN', 'ARTIFACT_RUNTIME_TOKEN'],
        'registry': ['REGISTRY_OPERATOR_TOKEN', 'WORKER_REGISTRY_TOKEN']}
    for name, settings in (('runtime', runtime), ('artifact', artifact), ('registry', registry)):
        owners[name]['configuration'] = str(write(output / (name + '.json'), settings))
        owners[name]['secret_references'] = references[name]
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    identity = TLSIdentity.create(bundle / 'tls', installation_id, 'C:/Program Files/Git/usr/bin/openssl.exe')
    with ExitStack() as stack:
        ports = {}
        for name in ('runtime', 'artifact'):
            probe = stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind(('127.0.0.1', 0))
            ports[name] = probe.getsockname()[1]
        assert not set(ports.values()).intersection(dict(routes.ports).values())
    write(output / 'access.json', {'profile': 'local-tool-access-v1', 'identity_directory': str(identity.directory), 'ports': ports})
    native = {name: {'configuration': owners['runtime']['configuration'], 'source_lock': owners['runtime']['source_lock'],
        'scope': {'actor': 'admin', 'tenant': scope['tenant_id'], 'project': scope['project_id']}}
        for name in (('runtime-coordinate', 'runtime-deliver') if delivery else ('runtime-coordinate',))}
    write(output / 'native.json', {'profile': 'local-native-workers-v1', 'workers': native})
    return material, identity, ports


def bind_workers(output, bundle, material, identity, ports, run_id, label):
    config_root = bundle / label
    config_root.mkdir()
    workers, replicas = {}, {}
    for stage in ('seed', 'requests', 'collect', 'vary', 'evaluate'):
        name = 'synthetic-objectives' if stage == 'evaluate' else 'evolution-' + stage
        image = material['images']['evaluate' if stage == 'evaluate' else 'numeric']
        path = write(config_root / (stage + '.json'), {'actor_id': 'science-slot', 'scope': material['scope'],
            'run_id': run_id, 'image_sha256': image[7:],
            'runtime': {'endpoint': 'https://host.docker.internal:' + str(ports['runtime']), 'token_env': 'AMPHORA_RUNTIME_TOKEN'},
            'artifacts': {'endpoint': 'https://host.docker.internal:' + str(ports['artifact']), 'token_env': 'AMPHORA_ARTIFACT_TOKEN'}})
        profile = ToolProfile.pin(name, image, path, identity.certificate, ports['runtime'], ports['artifact'])
        workers[name] = {'image_id': image, 'configuration': str(path), 'certificate': str(identity.certificate)}
        replicas[name] = {'deployment_id': stage, 'replica_id': 'local-' + stage, 'binding_sha256': profile.fingerprint}
    write(output / (label + '-scientific.json'), {'profile': 'local-scientific-workers-v1', 'workers': workers})
    write(output / (label + '-catalog.json'), {'profile': 'local-tool-catalog-v1', 'scope': material['scope'],
                                            'worker_id': 'science-slot', 'replicas': replicas})
