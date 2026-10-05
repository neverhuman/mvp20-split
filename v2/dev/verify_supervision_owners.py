"""Installed Planning/Runtime/Data commit-before-reply-loss and replacement proof."""

import argparse
import base64
import copy
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import URL

from campaign_context_fixture.support import environment
from check_boundaries import ROOT
from postgres_fixture import owned_state
from supervision_owner_fixture.hosts import LostReplyProxy, Owner


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return path


def verify(output, installation, data_python):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1'
    output, installation, data_python = output.absolute(), installation.absolute(), data_python.absolute()
    proof = json.loads((installation / 'manifest.json').read_bytes())
    assert proof['status'] == 'passed'
    assert proof['owners']['runtime']['version'] == '0.29.0' and proof['owners']['planning']['version'] == '0.72.0'
    output.mkdir(parents=True, exist_ok=False)
    tests = output / 'root'
    shutil.copytree(installation / 'root', tests, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for relative in ('services/campaign_runtime/tests/supervision_api/owner_worker.py',
                     'services/agent_planning/tests/supervision_client/owner_worker.py'):
        shutil.copyfile(ROOT / relative, tests / relative)
    base = environment()
    fixture = owned_state()
    host, port = fixture['endpoint'].split(':')
    urls = {owner: URL.create('postgresql+psycopg', username=owner + '_service', password=fixture['password'],
            host=host, port=int(port), database=fixture['database']).render_as_string(hide_password=False)
            for owner in ('runtime', 'planning')}
    urls['data'] = URL.create('postgresql+psycopg', username='artifact_service', password=fixture['password'],
        host=host, port=int(port), database=fixture['database']).render_as_string(hide_password=False)
    tokens = {name: secrets.token_hex(32) for name in ('peer', 'data', 'reader')}
    scope = {'tenant_id': 'supervisor-owner-proof', 'project_id': uuid.uuid4().hex}
    state = write(output / 'state.json', {'scope': scope})
    pythons = {owner: {label: installation / owner / label / 'Scripts/python.exe' for label in ('initial', 'replacement')}
               for owner in ('runtime', 'planning')}
    check = subprocess.run([str(data_python), '-I', '-c',
        "from importlib.metadata import version; assert version('amphora-data-artifacts') == '0.29.0'"],
        env=base, cwd=output, capture_output=True, timeout=20, check=False)
    assert check.returncode == 0, 'Current installed Data owner required'
    stages, owners, proxies, pids = {}, {}, {}, {}

    def stage(owner, mode, label='initial', endpoint=None):
        area = tests / ('services/campaign_runtime/tests/supervision_api' if owner == 'runtime' else
                        'services/agent_planning/tests/supervision_client')
        result = output / f'{owner}-{label}-{mode}.json'
        env = {**base, 'SUPERVISOR_OWNER_STATE': str(state), 'SUPERVISOR_OWNER_OUTPUT': str(result),
               'SUPERVISOR_OWNER_MODE': mode, 'SUPERVISOR_PEER_TOKEN': tokens['peer'],
               'SUPERVISOR_' + owner.upper() + '_SQL': urls[owner]}
        if endpoint is not None:
            env['SUPERVISOR_' + ('PLANNING' if owner == 'runtime' else 'RUNTIME') + '_ENDPOINT'] = endpoint
        process = subprocess.run([str(pythons[owner][label]), '-I', '-m', 'pytest', str(area / 'owner_worker.py'),
            '--confcutdir=' + str(area), '--import-mode=importlib', '-q', '--tb=short'],
            cwd=output, env=env, capture_output=True, text=True, encoding='utf-8', timeout=90, check=False,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        (output / f'{owner}-{label}-{mode}.log').write_text(process.stdout + process.stderr, encoding='utf-8')
        assert process.returncode == 0, 'Supervisor owner stage failed; inspect stage log'
        stages[f'{owner}-{label}-{mode}'] = json.loads(result.read_bytes())
        print(json.dumps({'owner': owner, 'stage': mode, 'installation': label}), flush=True)
        return stages[f'{owner}-{label}-{mode}']

    def start(name, label='initial'):
        if name in owners:
            owners[name].close()
        if name == 'planning':
            env = {**base, 'AMPHORA_PLANNING_DATABASE_URL': urls['planning'],
                   'AMPHORA_PLANNING_SUPERVISION_CREDENTIALS': json.dumps([{'token': tokens['peer'],
                    'actor_id': planning_actor, 'scope': scope, 'actions': ['record_requests', 'read_attempts']}])}
            owner = Owner(pythons[name][label], 'amphora_agent_planning.supervision_api', None, env, tokens['peer'], output)
        else:
            env = {**base, 'OWNER_SQL': urls[name], 'OWNER_TOKEN': tokens['data'] if name == 'data' else tokens['peer'],
                   'CAPTURE_READER_TOKEN': tokens['reader']}
            module = 'amphora_data_artifacts' if name == 'data' else 'amphora_campaign_runtime'
            owner = Owner(data_python if name == 'data' else pythons[name][label], module,
                          output / (name + '.json'), env, env['OWNER_TOKEN'], output)
        owners[name] = owner
        pids.setdefault(name, []).append(owner.process.pid)
        if name in proxies:
            proxies[name].target = owner.endpoint

    try:
        stage('runtime', 'bootstrap')
        data = json.loads(state.read_bytes())
        planning_actor = data['response_envelope']['identity']['actor_id']
        original_capture = data['response_envelope']['payload']['capture']
        # Literal wire fixtures use a placeholder. Actual Data requires a registered
        # validator identity; use its bounded JSON-object fixture profile.
        original_capture['schema_ref'] = {'schema_id': 'fixture.supervision-capture', 'version': '1',
                                          'sha256': hashlib.sha256(b'{"type":"object"}').hexdigest()}
        profile = {'media_type': original_capture['media_type'], **original_capture['schema_ref']}
        storage = output / 'bytes'
        storage.mkdir()
        write(output / 'data.json', {'database_url_env': 'OWNER_SQL', 'storage_root': str(storage),
            'profiles': [profile], 'acquisition': True, 'limits': {'max_bytes': 65536, 'scope_bytes': 1048576},
            'principals': [{'token_env': 'OWNER_TOKEN', 'actor_id': 'fixture', 'scope': scope,
                'actions': ['upload', 'finalize', 'read', 'acquire', 'source_history', 'manage_source_rights']},
                {'token_env': 'CAPTURE_READER_TOKEN', 'actor_id': 'reader', 'scope': scope, 'actions': ['read']}]})
        start('data')
        content = {k: original_capture[k] for k in ('sha256', 'size_bytes', 'media_type', 'schema_ref')}
        def artifact_command(family, key, payload):
            return {'identity': {'scope': scope, 'actor_id': 'fixture', 'command_family': family,
                                 'command_id': key}, 'payload': payload}
        upload = owners['data'].call('POST', '/v1/uploads', artifact_command('artifacts.begin_upload', 'capture.begin', {'content': content}))
        owners['data'].call('PUT', '/v1/uploads/' + upload['upload_id'] + '/content', base64.b64decode(data['capture']))
        artifact = owners['data'].call('POST', '/v1/artifacts/finalize', artifact_command('artifacts.finalize', 'capture.finalize',
            {'upload_id': upload['upload_id'], 'content': content}))['artifact']
        data['response_envelope']['payload']['capture'] = artifact
        write(state, data)
        rights = {'wire_version': '1', 'reference': {'scope': scope, 'rights_id': 'capture', 'revision': 1},
                  'supersedes': None, 'status': 'granted', 'allowed_uses': ['read', 'process'], 'expires_at': None,
                  'retention': 'retain_audit_payload'}
        owners['data'].call('POST', '/v1/acquisition/rights', rights)
        owners['data'].call('POST', '/v1/acquisition/prepare', {'wire_version': '1',
            'reference': {'scope': scope, 'source_id': 'capture', 'revision_id': 'r1', 'raw': artifact},
            'delivery': {'issuer_id': 'fixture', 'delivery_id': 'capture-source'},
            'method': {'connector_id': 'fixture', 'connector_version': '1', 'configuration_sha256': hashlib.sha256(b'{}').hexdigest(),
                       'format': 'utf8_document'}, 'rights': rights['reference'], 'supersedes': None, 'completeness': 'unknown'})
        fixture_run = json.loads((ROOT / 'services/campaign_runtime/tests/fixtures/prepared-run.json').read_bytes())['payload']
        def rescope(value):
            if isinstance(value, dict):
                if set(value) == {'tenant_id', 'project_id'}:
                    value.update(scope)
                for item in value.values():
                    rescope(item)
            elif isinstance(value, list):
                for item in value:
                    rescope(item)
        rescope(fixture_run)
        runtime_config = {'database_url_env': 'OWNER_SQL', 'fixtures': [fixture_run], 'principals': [
            {'token_env': 'OWNER_TOKEN', 'actor_id': planning_actor, 'scope': scope,
             'actions': ['read', 'supervise_respond', 'supervise_cancel']}],
            'supervision': {'capture_data': {'endpoint': owners['data'].endpoint, 'token_env': 'CAPTURE_READER_TOKEN'}}}
        write(output / 'runtime.json', runtime_config)
        start('planning')
        start('runtime')
        proxies['planning'] = LostReplyProxy(owners['planning'].endpoint, '/v1/supervision/requests')
        proxies['runtime'] = LostReplyProxy(owners['runtime'].endpoint, '/v1/supervision/responses')
        stage('runtime', 'send_request', endpoint=proxies['planning'].endpoint)
        request = stage('runtime', 'recover_request', 'replacement', proxies['planning'].endpoint)
        assert request['receipt'] == proxies['planning'].dropped[0]
        stage('planning', 'send_response', endpoint=proxies['runtime'].endpoint)
        first = stage('planning', 'recover_response', 'replacement', proxies['runtime'].endpoint)
        assert first['response_receipt'] == proxies['runtime'].dropped[0]
        before = stage('runtime', 'inspect')
        start('data', 'replacement')
        runtime_config['supervision']['capture_data']['endpoint'] = owners['data'].endpoint
        write(output / 'runtime.json', runtime_config)
        start('planning', 'replacement')
        start('runtime', 'replacement')
        after = stage('runtime', 'inspect', 'replacement')
        assert before == after
        rights2 = copy.deepcopy(rights)
        rights2.update(supersedes=rights['reference'], allowed_uses=['read'])
        rights2['reference']['revision'] = 2
        owners['data'].call('POST', '/v1/acquisition/rights', rights2)
        replay = stage('planning', 'replay', 'replacement', proxies['runtime'].endpoint)
        assert replay == first
        stage('planning', 'fresh_denied', 'replacement', proxies['runtime'].endpoint)
        rights3 = copy.deepcopy(rights)
        rights3.update(supersedes=rights2['reference'])
        rights3['reference']['revision'] = 3
        owners['data'].call('POST', '/v1/acquisition/rights', rights3)
        stage('planning', 'fresh_regranted', 'replacement', proxies['runtime'].endpoint)
        assert len(proxies['planning'].dropped) == len(proxies['runtime'].dropped) == 1
    finally:
        try:
            if state.exists():
                stage('runtime', 'cleanup', 'replacement')
        finally:
            for proxy in proxies.values():
                proxy.close()
            for owner in owners.values():
                owner.close()
    write(output / 'manifest.json', {'status': 'passed', 'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'scope': scope, 'owners': pids, 'stages': stages, 'proxy_records': {name: proxy.records for name, proxy in proxies.items()},
        'limits': ['Synthetic capture and test-owned dispatch; no provider call or B2 execution winner',
                   'Actual installed owner HTTP and retained SQL; no reset or migration',
                   'Replacement of this implementation, not an independently authored rewrite']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--installation', type=Path, required=True)
    parser.add_argument('--data-python', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation, args.data_python)
