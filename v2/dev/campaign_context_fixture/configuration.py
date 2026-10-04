"""Fresh synthetic owner configurations using only public fixture documents."""

import json
import shutil

from planning_knowledge_fixture import rescope


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return path


def principals(scope, actions, denied):
    return [
        {'token_env': 'CTX_TOKEN', 'actor_id': 'fixture', 'scope': scope, 'actions': actions},
        {'token_env': 'CTX_DENIED', 'actor_id': 'denied', 'scope': scope, 'actions': denied},
        {'token_env': 'CTX_FOREIGN', 'actor_id': 'fixture', 'scope': dict(scope, project_id='foreign'), 'actions': actions},
    ]


def registry(root, output, scope):
    value = {'database_url_env': 'CTX_REGISTRY_DB', 'principals': principals(scope, ['read', 'register', 'activate'], ['register']),
        'resources': {'architecture': 'x86_64', 'operating_system': 'windows', 'cpu_millicores': 4000,
            'memory_mib': 4096, 'gpu_count': 0, 'timeout_seconds': 300, 'max_parallel_invocations': 8, 'max_batch_size': 128}}
    return write(output / 'registry.json', value)


def runtime(root, output, scope):
    cases = json.loads((root / 'contracts/fixtures/v2/executable_cases.json').read_bytes())
    lock = next(c['payload']['document']['lock']['tools'][0] for c in cases if c['model'] == 'campaigns.execution-plan' and c['valid'])
    definition = next(c['payload'] for c in cases if c['model'] == 'campaigns.definition' and c['valid'])
    rescope(definition, scope)
    write(output / 'definition.json', definition)
    source = root / 'services/campaign_runtime/tests/fixtures/compiler'
    for name in ('numeric-release.json', 'input.json', 'output.json'):
        shutil.copyfile(source / name, output / name)
    value = {'database_url_env': 'CTX_RUNTIME_DB', 'principals': principals(scope, ['read'], ['cancel']),
        'fixtures': [], 'authoring': True, 'graphs': [{'definition': 'definition.json',
            'releases': [{'descriptor': 'numeric-release.json', 'lock': lock}],
            'schemas': [{'schema_ref': lock[name + '_schemas'][0]['schema_ref'], 'path': name + '.json'} for name in ('input', 'output')]}],
        'artifacts': {'runtime_owner': 'fixture-runtime', 'reserve_endpoint': 'http://127.0.0.1:1', 'token_env': 'CTX_TOKEN'}}
    return write(output / 'runtime.json', value), lock, json.loads((output / 'numeric-release.json').read_bytes())


def data(root, output, scope, backend):
    profiles = json.loads((root / 'services/data_artifacts/config.example.json').read_bytes())['profiles']
    storage = output / 'bytes'
    storage.mkdir()
    actions = ['upload', 'finalize', 'read', 'acquire', 'source_history', 'manage_source_rights',
               'representation_manage', 'representation_read', 'representation_encode']
    value = {'database_url_env': 'CTX_DATA_DB', 'storage_root': str(storage), 'profiles': profiles,
        'acquisition': True, 'representations': True, 'limits': {'max_bytes': 65536, 'scope_bytes': 1048576},
        'retrieval': {'endpoint': backend['endpoint'], 'token_env': 'CTX_QDRANT'},
        'principals': principals(scope, actions, ['upload'])}
    return write(output / 'data.json', value), profiles[0]


def knowledge(output, scope, prepared):
    value = {'database_url_env': 'PLANNING_KNOWLEDGE_DATABASE',
        'principals': principals(scope, ['read_graph'], ['propose_graph']),
        'vocabulary': prepared['profile']['vocabulary'], 'policy': prepared['policy_definition'],
        'data': {'endpoint': 'http://127.0.0.1:1', 'token_env': 'CTX_TOKEN'},
        'research': {'endpoint': 'http://127.0.0.1:1', 'token_env': 'CTX_TOKEN'}}
    return write(output / 'knowledge.json', value)
