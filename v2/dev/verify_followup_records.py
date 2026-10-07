"""Retain exact synthetic follow-up criteria through isolated Data/Research HTTP owners."""

import argparse
import hashlib
import json
import os
import secrets
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import URL

from campaign_context_fixture.support import Owner, environment
from postgres_fixture import owned_state


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return path


def verify(installation, output):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1', 'Explicit existing fixture opt-in required'
    installation, output = installation.absolute(), output.absolute()
    manifest = json.loads((installation / 'manifest.json').read_bytes())
    assert manifest['status'] == 'installed_only'
    output.mkdir(parents=True, exist_ok=False)
    (output / 'bytes').mkdir()
    scope = {'tenant_id': 'followup-acceptance', 'project_id': uuid.uuid4().hex}
    fixture = owned_state()
    host, port = fixture['endpoint'].split(':')
    token = secrets.token_hex(32)
    processes = []
    profile = {'media_type': 'text/plain', 'schema_id': 'followup.synthetic-text', 'version': '1',
               'sha256': hashlib.sha256(b'{"type":"string"}').hexdigest()}
    records = {}
    try:
        for name, module, role, actions in [
            ('artifact', 'amphora_data_artifacts', 'artifact_service', ['read', 'upload', 'finalize']),
            ('research', 'amphora_research', 'research_service', ['declare_question', 'declare_evidence_need', 'read_declarations']),
        ]:
            config = {'database_url_env': 'FOLLOWUP_OWNER_DATABASE_URL', 'principals': [
                {'token_env': 'FOLLOWUP_OWNER_TOKEN', 'actor_id': 'operator', 'scope': scope, 'actions': actions}]}
            if name == 'artifact':
                config.update(storage_root=str(output / 'bytes'), profiles=[profile])
            else:
                config['declarations'] = True
            path = write(output / (name + '.json'), config)
            database = URL.create('postgresql+psycopg', username=role, password=fixture['password'],
                host=host, port=int(port), database=fixture['database']).render_as_string(hide_password=False)
            owner = Owner(Path(manifest['owners'][name]['python']), module, path,
                {**environment(), 'FOLLOWUP_OWNER_DATABASE_URL': database, 'FOLLOWUP_OWNER_TOKEN': token}, token, output)
            processes.append(owner)
        data, research = processes
        body = b'Synthetic software acceptance: preserve uncertainty and exact criterion identity across campaigns.'
        schema = {key: profile[key] for key in ('schema_id', 'version', 'sha256')}
        content = {'sha256': hashlib.sha256(body).hexdigest(), 'size_bytes': len(body),
                   'media_type': 'text/plain', 'schema_ref': schema}

        def command(family, payload):
            return {'identity': {'scope': scope, 'actor_id': 'operator', 'command_id': uuid.uuid4().hex,
                                 'command_family': family}, 'payload': payload}

        upload = data.call('POST', '/v1/uploads', command('artifacts.begin_upload', {'content': content}))
        data.call('PUT', '/v1/uploads/' + upload['upload_id'] + '/content', body)
        artifact = data.call('POST', '/v1/artifacts/finalize', command('artifacts.finalize',
            {'upload_id': upload['upload_id'], 'content': content}))['artifact']
        question = {'wire_version': '1', 'reference': {'scope': scope, 'question_id': 'followup-question', 'revision': 1},
            'objective': 'Improve the next synthetic campaign while retaining unresolved points.', 'applicability': artifact,
            'criteria': [{'criterion_id': name, 'description': text} for name, text in [
                ('repeatability', 'Can the synthetic observation be repeated?'),
                ('applicability', 'Does the selected context support this interpretation?'),
                ('coverage', 'Which observations remain missing?')]], 'supersedes': None}
        need = {'wire_version': '1', 'reference': {'scope': scope, 'need_id': 'followup-need', 'revision': 1},
            'question': question['reference'], 'criterion_ids': [row['criterion_id'] for row in question['criteria']],
            'method': schema, 'required_context': artifact, 'supersedes': None}
        for path, value in [('questions', question), ('evidence-needs', need)]:
            research.call('POST', '/v1/' + path, value)
            assert research.call('POST', '/v1/' + path + '/read', value['reference']) == value
        records = {'scope': scope, 'artifact': artifact, 'question': question, 'need': need,
            'criteria': [{'question': question['reference'], 'need': need['reference'],
                          'criterion_id': row['criterion_id'], 'assessment': None} for row in question['criteria']]}
        write(output / 'records.json', records)
    finally:
        for owner in reversed(processes):
            owner.close()
    write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'scope': scope, 'criteria': len(records['criteria']), 'owners_stopped': len(processes),
        'versions': {key: value['version'] for key, value in manifest['owners'].items() if key in {'artifact', 'research'}},
        'limits': ['Exact retained synthetic owner records only', 'Assessment intentionally unselected',
                   'Proposal/subsequent campaign and browser qualification pending', 'Earlier intermittent feedback failure unresolved']})
    print('Actual isolated Data/Research retained three exact unassessed criteria; owners stopped', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.installation, args.output)
