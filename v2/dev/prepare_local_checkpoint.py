"""Prepare immutable local checkpoint configs with real public artifacts; no model calls."""

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
from local_numeric_configuration import write
from local_records_controller import RecordsController
from verify_local_owner_records import Scenario


def prepare(output, records_directory, source_manifest, planning_installation):
    output.mkdir(parents=True, exist_ok=False)
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    original = LocalState.snapshot(root)
    vault = (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    records = json.loads((records_directory / 'records.json').read_bytes())
    scope = records['question']['reference']['scope']
    source = json.loads(source_manifest.read_bytes())
    runtime = Path(source['owners']['runtime']['installation']) / 'environment/Scripts/python.exe'
    planning = planning_installation / 'environment/Scripts/python.exe'
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment['PYTHONUTF8'] = '1'

    def export(python, script, action):
        result = subprocess.run([str(python), '-I', str(script), action, str(output)], env=environment,
            capture_output=True, text=True, encoding='utf-8', timeout=45,
            creationflags=subprocess.CREATE_NO_WINDOW)
        with (output / 'preparation.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == 0, 'Owner-local material export failed; inspect preparation.log'

    runtime_script = ROOT / 'services/campaign_runtime/tests/supervision_loop/owners/export_demo.py'
    planning_script = ROOT / 'services/agent_planning/tests/checkpoint_openai/export_demo.py'
    export(runtime, runtime_script, 'profiles')
    export(planning, planning_script, 'profile')
    profiles = json.loads((output / 'profiles.json').read_bytes())
    profile = json.loads((output / 'planning-profile.json').read_bytes())
    data = json.loads((records_directory / 'artifact.json').read_bytes())
    data['profiles'] += profiles

    def principal(actor, reference, actions):
        return {'actor_id': actor, 'scope': scope, 'token_env': 'AMPHORA_' + reference, 'actions': actions}

    data['principals'] += [principal('runtime', 'RUNTIME_ARTIFACT_TOKEN', ['read', 'upload', 'finalize', 'retention', 'source_history']),
        principal('planning', 'PLANNING_DATA_TOKEN', ['read', 'upload', 'finalize', 'source_history'])]
    data['runtime'] = {'owner': 'runtime', 'endpoint': routes.endpoint('runtime') + '/v1/completion-intents/outcome',
                       'token_env': 'AMPHORA_ARTIFACT_RUNTIME_TOKEN'}
    data_path = write(output / 'artifact.json', data)
    owners = {'artifact': dict(source['owners']['artifact'], configuration=str(data_path),
        secret_references=['ARTIFACT_OPERATOR_TOKEN', 'KNOWLEDGE_DATA_TOKEN', 'RUNTIME_ARTIFACT_TOKEN', 'PLANNING_DATA_TOKEN', 'ARTIFACT_RUNTIME_TOKEN'])}
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    tokens = CredentialVault(root / 'credentials.dpapi', original['deployment_id']).load().environment(['ARTIFACT_OPERATOR_TOKEN'])
    controller = RecordsController(root, output, routes)
    try:
        controller.start()
        scenario = Scenario(controller, tokens, scope, output)
        text_schema = {key: value for key, value in next(p for p in profiles if p['media_type'] == 'text/plain').items() if key != 'media_type'}
        objective = scenario.publish(b'Synthetic engineering only. At the bounded parameter checkpoint, propose integer a=7 within the declared range when permitted. This checks software control, not scientific validity.', text_schema, 'text/plain')
        prompt = scenario.publish((output / 'prompt.txt').read_bytes(), text_schema, 'text/plain')
        model_config = scenario.publish(b'Approved synthetic engineering scope only. One attempt per request; no external tools. Retain unknown and failed usage. Six reservations and USD0.50 maximum for this project.', text_schema, 'text/plain')
        model = {'provider_id': 'openai', 'model_id': profile['model'], 'model_revision': profile['model'],
                 'tokenizer': profile['tokenizer'], 'context_window_tokens': 400000, 'configuration': model_config}
        limits = {'max_input_tokens': 65536, 'max_output_tokens': 2048, 'max_attempts': 1, 'total_tokens': 67584,
                  'total_accounting_units': 500000000, 'accounting_unit': 'usd_nanodollars'}
        actions = ['abstain', 'propose_campaign', 'request_evidence']
        write(output / 'template-input.json', {'profile': 'planning-supervision-budget-template.v1', 'scope': scope,
            'model': model, 'prompt': prompt, 'output_schema': profile['output_schema'], 'allowed_actions': actions,
            'limits': limits, 'per_attempt_accounting_units': 58368000})
        export(planning, planning_script, 'template')
        template_schema = {k: v for k, v in next(p for p in profiles if p['schema_id'] == 'demo.budget-template').items() if k not in ('media_type', 'schema_path')}
        template = scenario.publish((output / 'template.json').read_bytes(), template_schema)
        write(output / 'recipe-input.json', {'profile': 'runtime-supervision-recipe.v1', 'scope': scope,
            'objective': objective, 'prompt': prompt, 'model': model, 'budget_policy': template,
            'entries': [], 'omissions': [], 'allowed_actions': actions, 'limits': limits})
        export(runtime, runtime_script, 'compile')
        final = controller.drain()
    finally:
        controller.close()
    # Add the reviewed owners only after all public references are durable and Data has drained.
    compiled = json.loads((output / 'compiled.json').read_bytes())
    peer = {'endpoint': routes.endpoint('artifact'), 'token_env': 'AMPHORA_RUNTIME_ARTIFACT_TOKEN'}
    runtime_config = {'database_url_env': 'AMPHORA_RUNTIME_DATABASE_URL', 'fixtures': [], 'graphs': [compiled['graph']],
        'principals': [principal('operator', 'RUNTIME_OPERATOR_TOKEN', ['read', 'admit', 'maintain', 'deliver', 'cancel']),
            principal('planning', 'PLANNING_RUNTIME_TOKEN', ['read', 'supervise_respond']),
            principal('artifact', 'ARTIFACT_RUNTIME_TOKEN', ['outcome'])],
        'artifacts': {'runtime_owner': 'runtime', 'reserve_endpoint': routes.endpoint('artifact') + '/v1/reservations',
                      'token_env': 'AMPHORA_RUNTIME_ARTIFACT_TOKEN'},
        'bindings': peer, 'projections': peer, 'supervision': {'capture_data': peer},
        'supervision_admission': {'policies': ['policy.json'], 'recipes': ['recipe.json']},
        'inspection': {'cursor_key_env': 'AMPHORA_CURSOR_KEY'}}
    owners['runtime'] = dict(source['owners']['runtime'], configuration=str(write(output / 'runtime.json', runtime_config)),
        secret_references=['RUNTIME_OPERATOR_TOKEN', 'RUNTIME_ARTIFACT_TOKEN', 'ARTIFACT_RUNTIME_TOKEN',
                           'PLANNING_RUNTIME_TOKEN', 'RUNTIME_PLANNING_TOKEN', 'CURSOR_KEY'])
    planning_config = {'principals': [principal('planning', 'RUNTIME_PLANNING_TOKEN', ['record_requests', 'read_attempts']),
                                    principal('operator', 'PLANNING_OPERATOR_TOKEN', ['read_attempts'])]}
    owners['planning'] = {'installation': str(planning_installation),
        'source_lock': str(ROOT / 'services/agent_planning/uv.lock'),
        'configuration': str(write(output / 'planning.json', planning_config)),
        'secret_references': ['PLANNING_OPERATOR_TOKEN', 'RUNTIME_PLANNING_TOKEN', 'PLANNING_DATA_TOKEN', 'PLANNING_RUNTIME_TOKEN']}
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    runtime_worker = write(output / 'runtime-checkpoint.json', {'database_url_env': 'AMPHORA_RUNTIME_DATABASE_URL',
        'actor_id': 'operator', 'scope': scope, 'data': dict(peer, actor_id='runtime'),
        'planning': {'endpoint': routes.endpoint('planning'), 'token_env': 'AMPHORA_RUNTIME_PLANNING_TOKEN', 'actor_id': 'planning'}})
    planning_worker = write(output / 'planning-checkpoint.json', {'database_url_env': 'AMPHORA_PLANNING_DATABASE_URL',
        'actor_id': 'planning', 'scope': scope, 'publisher_id': 'local-data',
        'data': {'endpoint': routes.endpoint('artifact'), 'token_env': 'AMPHORA_PLANNING_DATA_TOKEN'},
        'runtime': {'endpoint': routes.endpoint('runtime'), 'token_env': 'AMPHORA_PLANNING_RUNTIME_TOKEN'},
        'templates': [{'reference': template, 'path': 'template.json'}], 'provider': 'openai_checkpoint_v1',
        'live': {'key_env': 'AMPHORA_OPENAI_API_KEY', 'egress': 'approved_synthetic_engineering_only', 'timeout_seconds': 45},
        'timeout_seconds': 60})
    workers = {name: {'configuration': owners['runtime']['configuration'], 'source_lock': owners['runtime']['source_lock'],
        'scope': {'actor': 'operator', 'tenant': scope['tenant_id'], 'project': scope['project_id']}}
        for name in ('runtime-coordinate', 'runtime-deliver')}
    for name, owner, path in [('runtime-checkpoint', 'runtime', runtime_worker), ('planning-checkpoint', 'planning', planning_worker)]:
        workers[name] = {'configuration': str(path), 'source_lock': owners[owner]['source_lock'], 'scope': None}
    write(output / 'native.json', {'profile': 'local-native-workers-v1', 'workers': workers})
    shutil.copyfile(records_directory / 'records.json', output / 'research-knowledge-records.json')
    assert LocalState.snapshot(root) == original and (root / 'credentials.dpapi').read_bytes() == vault
    write(output / 'prepared.json', {'scope': scope, 'objective': objective, 'template': template,
        'compiled': compiled, 'data_drain': final, 'provider_calls': 0,
        'limits': ['Preparation only; worker configuration/readiness and model/browser execution remain unverified',
                   'Existing owner records retained; current minimal checkpoint does not yet consume Knowledge/Research']})
    print('Checkpoint materials published and owner-local policy compiled; zero provider calls', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'records-directory', 'source-manifest', 'planning-installation'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    prepare(args.output.absolute(), args.records_directory.absolute(), args.source_manifest.absolute(), args.planning_installation.absolute())
