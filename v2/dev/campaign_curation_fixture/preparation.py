"""Immutable owner and managed-launch configuration on a separate restored root."""
import json
import shutil
import socket
from contextlib import ExitStack
from pathlib import Path

from amphora_deployment.campaign_launch.credentials import provision_launch_credential
from amphora_deployment.campaign_launch.profile import profile_digest
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.scientific_workers.profiles import ToolProfile
from amphora_deployment.tool_access import TLSIdentity
from local_numeric_configuration import write


def relative_inputs(restored, output, value):
    """Native workers pin bounded relative inputs; retain their exact bytes."""
    source = (restored / 'configuration-inputs').resolve()
    target = output / 'configuration-inputs'
    if not target.exists():
        shutil.copytree(source, target)
    def relocate(item):
        if isinstance(item, dict):
            return {key: relocate(child) for key, child in item.items()}
        if isinstance(item, list):
            return [relocate(child) for child in item]
        if isinstance(item, str) and Path(item).is_absolute():
            path = Path(item).resolve()
            if path.parent == source:
                assert (target / path.name).read_bytes() == path.read_bytes()
                return 'configuration-inputs/' + path.name
        return item
    return relocate(value)


def prepare(root, restored, output, planning, deployment, gateway):
    assert not output.exists()
    evidence = json.loads((restored / 'restore.json').read_bytes())
    state = LocalState.snapshot(root)
    assert evidence['target_deployment_id'] == state['deployment_id']
    assert json.loads((restored / 'planning-forward.json').read_bytes())['status'] == 'passed'
    routes = Routes.load(root)
    output.mkdir()
    v2 = Path(__file__).absolute().parents[2]
    owners = json.loads((restored / 'owners.json').read_bytes())['owners']
    configs = {name: relative_inputs(restored, output, json.loads(Path(row['configuration']).read_bytes()))
               for name, row in owners.items()}
    scope = next(p['scope'] for p in configs['runtime']['principals'] if p['actor_id'] == 'admin')
    configs['planning'] = {'curation_policies': ['internal-curation-v1'], 'principals': [{'actor_id': 'admin', 'scope': scope,
        'token_env': 'AMPHORA_PLANNING_OPERATOR_TOKEN',
        'actions': ['record_curations', 'read_curations', 'read_capabilities', 'read_campaign_origin', 'read_attempts']}]}
    owners['planning']['installation'] = str(planning)
    owners['planning']['source_lock'] = str(v2 / 'services/agent_planning/uv.lock')
    for name, config in configs.items():
        owners[name]['configuration'] = str(write(output / (name + '.json'), config))
    public = output / 'public'; public.mkdir()
    for name in ('index.html', 'app.js', 'app.css'):
        shutil.copyfile(v2 / 'studio/dist/local' / name, public / name)
    with ExitStack() as stack:
        ports = {}
        for name in ('runtime', 'artifact', 'launch'):
            probe = stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind(('127.0.0.1', 0)); ports[name] = probe.getsockname()[1]
        assert not set(ports.values()).intersection(dict(routes.ports).values())
    launch_port = ports.pop('launch')
    identity = TLSIdentity.create(root / 'qualification-tls', state['deployment_id'],
                                  'C:/Program Files/Git/usr/bin/openssl.exe')
    write(output / 'access.json', {'profile': 'local-tool-access-v1',
        'identity_directory': str(identity.directory), 'ports': ports})
    native = {name: {'configuration': owners['runtime']['configuration'],
        'source_lock': owners['runtime']['source_lock'],
        'scope': {'actor': 'admin', 'tenant': scope['tenant_id'], 'project': scope['project_id']}}
        for name in ('runtime-coordinate', 'runtime-deliver')}
    write(output / 'native.json', {'profile': 'local-native-workers-v1', 'workers': native})
    tool = next(t['binding'] for t in configs['runtime']['tools'] if t['binding']['capability_id'] == 'numeric.search-seed')
    image = 'sha256:' + tool['image_sha256']
    path = write(root / 'qualification-seed.json', {'actor_id': 'science-slot', 'scope': scope,
        'run_id': 'awaiting-admission', 'image_sha256': tool['image_sha256'],
        'runtime': {'endpoint': 'https://host.docker.internal:' + str(ports['runtime']), 'token_env': 'AMPHORA_RUNTIME_TOKEN'},
        'artifacts': {'endpoint': 'https://host.docker.internal:' + str(ports['artifact']), 'token_env': 'AMPHORA_ARTIFACT_TOKEN'}})
    bound = ToolProfile.pin('evolution-seed', image, path, identity.certificate, ports['runtime'], ports['artifact'])
    write(output / 'scientific.json', {'profile': 'local-scientific-workers-v1', 'workers': {
        'evolution-seed': {'image_id': image, 'configuration': str(path), 'certificate': str(identity.certificate)}}})
    write(output / 'catalog.json', {'profile': 'local-tool-catalog-v1', 'scope': scope,
        'worker_id': 'science-slot', 'replicas': {'evolution-seed': {'deployment_id': 'seed',
            'replica_id': 'curation-seed', 'binding_sha256': bound.fingerprint}}})
    policy = {'reference': {'profile_id': 'curation-integration', 'version': '1', 'sha256': '0' * 64},
        'scope': scope, 'title': 'Synthetic numerical successor integration', 'tools': [tool],
        'maximum_invocations': 4, 'maximum_deadline_seconds': 600}
    policy['reference']['sha256'] = profile_digest(policy)
    write(output / 'launch-profile.json', policy)
    write(output / 'launch.json', {'profile': 'local-campaign-launch-v1', 'actor_id': 'admin',
        'launch_profile': str(output / 'launch-profile.json'), 'scientific_manifest': str(output / 'scientific.json'),
        'catalog_manifest': str(output / 'catalog.json')})
    provision_launch_credential(root)
    gateway_config = {'profile': 'local-gateway-v1', 'public_directory': str(public),
        'peers': {name: {'endpoint': routes.endpoint(name), 'token_env': 'AMPHORA_' + name.upper() + '_OPERATOR_TOKEN'} for name in owners},
        'context': {'actor_id': 'admin', 'scope': scope, 'run_id': 'awaiting-admission', 'synthetic': True},
        'launcher_key_env': 'AMPHORA_GATEWAY_SESSION_KEY'}
    gateway_config['peers']['deployment'] = {'endpoint': 'http://127.0.0.1:' + str(launch_port), 'token_env': 'AMPHORA_LAUNCH_GATEWAY_TOKEN'}
    owners['gateway'] = {'installation': str(gateway), 'source_lock': str(v2 / 'services/local_gateway/uv.lock'),
        'configuration': str(write(output / 'gateway.json', gateway_config)),
        'secret_references': ['GATEWAY_SESSION_KEY', 'LAUNCH_GATEWAY_TOKEN'] + [name.upper() + '_OPERATOR_TOKEN' for name in owners]}
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    write(output / 'launch-prepared.json', {'scope': scope, 'launch_port': launch_port,
        'deployment_python': str(deployment / 'environment/Scripts/python.exe'),
        'provider_calls': 0, 'status': 'prepared_not_started'})
    return output
