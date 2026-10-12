"""Actual six-owner synthetic curation, compiler and managed successor acceptance."""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.persistence.state import LocalState
from local_numeric_configuration import write
from .campaign import Campaign, seed_definition
from .publication import Publication
from .session import session


def filtered_environment():
    result = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    result['PYTHONUTF8'] = '1'
    return result


def planning_process(python, action, path, output, env=None):
    script = Path(__file__).with_name('planning.py')
    with (output / ('planning-' + action + '.log')).open('ab') as log:
        result = subprocess.run([str(python), '-I', str(script), action, str(path)],
            env=env or filtered_environment(), stdout=log, stderr=log, timeout=300,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert result.returncode == 0, 'Isolated Planning ' + action + ' failed; inspect owned log'


def publish_case(api, output, scope, runtime, material):
    retained = output / 'published-case.json'
    if retained.exists():
        return json.loads(retained.read_bytes())
    v2 = Path(__file__).absolute().parents[2]
    publication = Publication(api, scope)
    profile = next(row for row in json.loads((output / 'artifact.json').read_bytes())['profiles'] if row['media_type'] == 'text/plain')
    schema = {key: profile[key] for key in ('schema_id', 'version', 'sha256')}
    roots = {name: publication.publish(body, schema) for name, body in (
        ('objective', b'Exercise a synthetic numerical seed campaign, carry its exact retained result, and run the next campaign.'),
        ('policy', b'Synthetic numerical integration only. No chemistry, live-model reasoning, scientific improvement or calibrated accuracy claim.'),
        ('configuration', b'Deterministic test-only provider adapter; zero external requests or charges.'),
        ('prompt', material['instructions'].encode()))}
    seed = next(row for row in runtime['tools'] if row['binding']['capability_id'] == 'numeric.search-seed')
    evaluator = next(row for row in runtime['tools'] if row['binding']['capability_id'] == 'synthetic.numeric-objectives')
    result = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--read-only', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', 'sha256:' + evaluator['binding']['image_sha256'], 'policy'],
        capture_output=True, timeout=30, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert result.returncode == 0 and len(result.stdout) <= 262144
    policy = publication.publish(result.stdout, next(row['schema_ref'] for row in evaluator['inputs'] if row['name'] == 'policy'),
                                 media_type='application/json')
    specification = json.loads((v2 / 'tools/evolution_search/tests/specification/synthetic_specification.json').read_bytes())
    specification['scope'] = scope
    specification['evaluator'].update(tool=evaluator['binding'], constraints=policy)
    specification['implementations'] = [{'name': 'numeric-search', 'version': seed['binding']['release'], 'sha256': seed['binding']['image_sha256']}]
    artifact = publication.publish(json.dumps(specification).encode(), seed['inputs'][0]['schema_ref'], media_type='application/json')
    value = {'roots': roots, 'specification': artifact, 'definition': seed_definition(scope, runtime, artifact)}
    write(retained, value)
    return value


def worker_configuration(api, output, scope, roots, material, attempt):
    v2 = Path(__file__).absolute().parents[2]
    raw = json.loads((v2 / 'services/agent_planning/tests/campaign_context/fixtures/request.json').read_bytes())
    raw.update(reference={'scope': scope, 'engagement_id': 'synthetic-curation-template'}, actor_id='admin', runtime_cut=None)
    context = raw['context']
    context.update(scope=scope, objective=roots['objective'], prompt=roots['prompt'], policy=roots['policy'],
        entries=[], omissions=[], output_schema=material['output_schema'], allowed_actions=['abstain', 'propose_campaign'])
    model = 'gpt-5.4-mini-2026-03-17'
    context['model'].update(provider_id='openai', model_id=model, model_revision=model,
        configuration=roots['configuration'], tokenizer=material['tokenizer'], context_window_tokens=400000)
    context['limits'].update(max_input_tokens=262144, max_output_tokens=8192, total_tokens=270336,
        max_attempts=1, total_accounting_units=250000000, accounting_unit='usd_nanodollars')
    write(attempt / 'curation-policy.json', {'profile': 'planning-curation-policy.v1', 'policy_id': 'internal-curation-v1',
        'template': raw, 'future': {'max_nodes': 64, 'max_scopes': 16, 'max_depth': 4, 'max_iterations': 32,
            'max_tool_timeout': 300, 'side_effects': ['pure']}, 'eligibility_context': 'synthetic-tests',
        'reservation_units': 250000000})
    registry = json.loads((output / 'registry.json').read_bytes())
    selection = {'profile': 'amphora-tool-selection-v1', 'scientific_profile': 'synthetic-only-v1', 'scope': scope,
        'resources': registry['resources'], 'permissions': {'allowed_egress_hosts': [], 'effects': ['pure']}}
    digest = hashlib.sha256(json.dumps(selection, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
    worker = {'database_url_env': 'CURATION_PLANNING_DATABASE', 'actor_id': 'admin', 'scope': scope,
        'worker_id': 'isolated-curation-worker', 'policies': ['curation-policy.json'], 'runtime_owner': 'runtime',
        'eligibility': {'owner_id': 'registry', 'actor_id': 'admin', 'policy_sha256': digest, 'maximum_age_seconds': 60}}
    for name in ('data', 'runtime', 'registry', 'knowledge', 'research'):
        owner = 'artifact' if name == 'data' else name
        worker[name] = {'endpoint': api.endpoints[owner], 'token_env': 'CURATION_' + name.upper() + '_TOKEN'}
    return write(attempt / 'curation-worker.json', worker)


def verify(root, output, *, diagnose=False):
    owners = json.loads((output / 'owners.json').read_bytes())['owners']
    python = Path(owners['planning']['installation']) / 'environment/Scripts/python.exe'
    material_path = output / 'planning-material.json'
    if not material_path.exists():
        planning_process(python, 'material', material_path, output)
    material = json.loads(material_path.read_bytes())
    scope = json.loads((output / 'launch-profile.json').read_bytes())['scope']
    profile = json.loads((output / 'launch-profile.json').read_bytes())['reference']
    runtime = json.loads((output / 'runtime.json').read_bytes())
    with session(root, output) as api:
        case = publish_case(api, output, scope, runtime, material)
        campaign = Campaign(api, output, scope)
        draft, validation = campaign.save(case['definition'])
        receipt, predecessor, sources = campaign.launch(validation, profile)
        # Request01 remains a terminal applicability rejection. Corrected operator
        # policy belongs to a separate original intent; never rewrite its capture.
        attempt = output / 'curation-02'; attempt.mkdir(exist_ok=True)
        worker_path = worker_configuration(api, output, scope, case['roots'], material, attempt)
        command = Campaign(api, attempt, scope).original('curation', 'planning.curate_campaign', {
            'direction': 'Retain the exact previous result as a carried input and exported comparison point while running another synthetic seed.',
            'policy_id': 'internal-curation-v1', 'context': {'predecessor': sources['predecessor'],
                'draft': {'scope': scope, **{key: draft['head'][key] for key in ('draft_id', 'revision', 'content_sha256')}},
                'knowledge': [], 'questions': [], 'needs': [], 'artifacts': [case['specification']]}})
        original = api.call('planning', '/v1/campaign-curations', command, allowed=(200, 202))
        write(attempt / 'curation-original-receipt.json', original)
        state = LocalState.snapshot(root)
        bundle = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load()
        password = bundle.environment(['PG_PLANNING_SERVICE_PASSWORD'])['PG_PLANNING_SERVICE_PASSWORD']
        env = filtered_environment()
        env['CURATION_PLANNING_DATABASE'] = 'postgresql+psycopg://planning_service:' + quote(password, safe='') + '@127.0.0.1:' + str(state['postgres']['port']) + '/amphora_local?connect_timeout=5'
        for name in ('data', 'runtime', 'registry', 'knowledge', 'research'):
            env['CURATION_' + name.upper() + '_TOKEN'] = api.tokens['artifact' if name == 'data' else name]
        if diagnose:
            planning_process(python, 'profile', worker_path, attempt, env)
            print('Read-only Planning compiler profile retained; no worker advanced', flush=True)
            return
        path = '/v1/campaign-curations/' + original['reference']['curation_id']
        current = api.call('planning', path)
        if current['receipt']['phase'] != 'ready':
            planning_process(python, 'run', worker_path, attempt, env)
        current = api.call('planning', path)
        write(attempt / 'curation-ready.json', current)
        assert current['receipt']['phase'] == 'ready'
        capture = (attempt / 'synthetic-provider-response.json').read_bytes()
        assert current['provider']['output_sha256'] == hashlib.sha256(capture).hexdigest()
        selected_draft = current['validated_draft']
        compiled = api.call('runtime', '/v1/definition-drafts/' + selected_draft['draft_id'] +
                            '?revision=' + str(selected_draft['revision']))
        assert compiled['definition'] == current['proposal']['outcome']['candidate']['definition']
        validation = api.call('runtime', '/v1/definition-validations/' + current['validated_draft']['validation_id'])
        selected = next(row for row in sources['sources'] if row['source'] == {'kind': 'run_output', 'port': 'result'})
        carried = [{'target_port': 'previous_result', 'source': selected['source'], 'expected_value_sha256': selected['value_sha256']}]
        child_receipt, child, child_sources = campaign.launch(validation, profile, predecessor=sources['predecessor'], carried=carried)
        lineage = api.call('runtime', '/v1/graph-runs/' + child['run_id'] + '/lineage')
        assert lineage['predecessor'] == sources['predecessor'] and lineage['carried'] == carried
        retained = next(row for row in child_sources['sources'] if row['source'] == {'kind': 'run_output', 'port': 'previous_result'})
        assert retained['value_sha256'] == selected['value_sha256']
        assert api.call('runtime', '/v3/graph-runs/' + predecessor['run_id']) == predecessor
        assert api.call('planning', '/v1/campaign-curations', command, allowed=(200, 202)) == original
        write(output / 'integrated-evidence.json', {'status': 'passed', 'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'scope': scope, 'predecessor': predecessor, 'successor': child, 'lineage': lineage,
            'successor_launch': child_receipt, 'curation': current, 'paid_provider_calls': 0,
            'limits': ['Deterministic synthetic Planning adapter, no live reasoning or science claim',
                'Actual six-owner public APIs, isolated SQL, numeric seed container and managed worker binding',
                'Replacement/failure and browser qualification remain separate P4.4 gates']})
    print('Actual synthetic curation/compiler/successor/worker integration passed and drained', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--diagnose', action='store_true')
    args = parser.parse_args()
    verify(args.root.absolute(), args.output.absolute(), diagnose=args.diagnose)
