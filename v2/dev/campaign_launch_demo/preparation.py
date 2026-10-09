"""Immutable configuration preparation, with no running-owner mutation."""
import copy
import json
import shutil
import uuid
from pathlib import Path

from amphora_deployment.campaign_launch.profile import profile_digest
from amphora_deployment.lifecycle.routes import Routes
from local_numeric_configuration import write


def pinned_definition(definition, admission):
    result = copy.deepcopy(definition)
    assert all(node['kind'] in {'invoke', 'finish'} for node in result['body']['nodes']), 'Only the original flat demo is supported'
    inputs = admission['payload']['inputs']
    values = {item['port']: item['value'] for item in inputs}
    assert len(values) == len(inputs) and set(values) == {port['name'] for port in result['body']['inputs']}
    assert all(value['kind'] == 'artifact' and value['artifact']['scope'] == result['scope'] for value in values.values())
    used = set()
    for node in result['body']['nodes']:
        for binding in node['inputs' if node['kind'] == 'invoke' else 'outputs']:
            source = binding['source']
            if source['kind'] == 'input':
                used.add(source['name'])
                binding['source'] = copy.deepcopy(values[source['name']])
    assert used == set(values), 'Every original input must remain represented'
    result['body']['inputs'] = []
    result['revision'] += 1
    return result


def prepare(root, source, installations, public, output, launch_port=57021):
    output = output.absolute(); output.mkdir(parents=True, exist_ok=False)
    routes = Routes.load(root)
    assert launch_port not in dict(routes.ports).values()
    evidence = json.loads((source / 'evidence.json').read_bytes())
    assert evidence['status'] == 'passed' and evidence['provider_calls'] == 0
    # Relative schemas/descriptors in Runtime/Data configurations remain exact.
    for path in source.glob('*.json'):
        shutil.copyfile(path, output / path.name)
    assets = output / 'public'; assets.mkdir()
    for name in ('index.html', 'app.js', 'app.css'):
        shutil.copyfile(public / name, assets / name)
    owners = json.loads((source / 'owners.json').read_bytes())['owners']
    runtime = json.loads((source / 'runtime.json').read_bytes())
    registry = json.loads((source / 'registry.json').read_bytes())
    runtime['authoring'] = True
    runtime['draft_registry'] = {'endpoint': routes.endpoint('registry'),
        'token_env': 'AMPHORA_RUNTIME_REGISTRY_TOKEN', 'actor_id': 'runtime-draft'}
    for principal in runtime['principals']:
        if principal['actor_id'] == 'admin':
            principal['actions'] = sorted(set(principal['actions']) | {'author', 'validate'})
    assert not any(row['actor_id'] == 'runtime-draft' for row in registry['principals'])
    registry['principals'].append({'token_env': 'AMPHORA_RUNTIME_REGISTRY_TOKEN', 'actor_id': 'runtime-draft',
        'scope': evidence['scope'], 'actions': ['read', 'resolve']})
    for owner, config in [('runtime', runtime), ('registry', registry)]:
        owners[owner]['configuration'] = str(write(output / (owner + '.json'), config))
        owners[owner]['secret_references'] = sorted(set(owners[owner]['secret_references']) | {'RUNTIME_REGISTRY_TOKEN'})
    owners['artifact']['configuration'] = str(output / 'artifact.json')
    native = json.loads((source / 'native.json').read_bytes())
    for worker in native['workers'].values(): worker['configuration'] = str(output / 'runtime.json')
    write(output / 'native.json', native)
    gateway = {'profile': 'local-gateway-v1', 'public_directory': str(assets),
        'peers': {name: {'endpoint': routes.endpoint(name), 'token_env': 'AMPHORA_' + name.upper() + '_OPERATOR_TOKEN'} for name in owners},
        'context': {'actor_id': 'admin', 'scope': evidence['scope'], 'run_id': evidence['run_id'], 'synthetic': True},
        'launcher_key_env': 'AMPHORA_GATEWAY_SESSION_KEY'}
    gateway['peers']['deployment'] = {'endpoint': 'http://127.0.0.1:' + str(launch_port), 'token_env': 'AMPHORA_LAUNCH_GATEWAY_TOKEN'}
    owners['gateway'] = {'installation': str((installations / 'gateway').absolute()),
        'source_lock': str((Path(__file__).resolve().parents[2] / 'services/local_gateway/uv.lock')),
        'configuration': str(write(output / 'gateway.json', gateway)),
        'secret_references': ['GATEWAY_SESSION_KEY', 'LAUNCH_GATEWAY_TOKEN'] + [name.upper() + '_OPERATOR_TOKEN' for name in owners]}
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    tools = [json.loads((source / (stage + '-descriptor.json')).read_bytes())['tool']['binding']
        for stage in ('hansen_solvency', 'arrhenius_viscosity')]
    policy = {'reference': {'profile_id': 'scientific-demo', 'version': '1', 'sha256': '0' * 64},
        'scope': evidence['scope'], 'title': 'Solvency and temperature-adjusted viscosity', 'tools': tools,
        'maximum_invocations': 8, 'maximum_deadline_seconds': 600}
    policy['reference']['sha256'] = profile_digest(policy)
    write(output / 'launch-profile.json', policy)
    write(output / 'launch.json', {'profile': 'local-campaign-launch-v1', 'actor_id': 'admin',
        'launch_profile': str(output / 'launch-profile.json'), 'scientific_manifest': str(source.absolute() / 'admitted-scientific.json'),
        'catalog_manifest': str(source.absolute() / 'admitted-catalog.json')})
    original = json.loads((source / 'admission.json').read_bytes())['command']
    definition = pinned_definition(json.loads((source / 'graph.json').read_bytes()), original)
    write(output / 'draft-save-command.json', {'encoding': 'amphora-command-v2', 'identity': {
        'actor_id': 'admin', 'scope': evidence['scope'], 'command_family': 'definition.save', 'command_id': uuid.uuid4().hex},
        'payload': {'draft_id': 'scientific-launch-' + uuid.uuid4().hex, 'expected_revision': 0,
            'title': 'Polymer screening — pinned synthetic parameters', 'definition': definition}})
    write(output / 'launch-prepared.json', {'scope': evidence['scope'], 'baseline_run': evidence['run_id'],
        'launch_port': launch_port, 'deployment_python': str((installations / 'deployment/environment/Scripts/python.exe').absolute()),
        'provider_calls': 0, 'status': 'prepared_not_started'})
    return output
