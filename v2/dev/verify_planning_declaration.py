"""Actual Data publication and original Planning decision binding after restart."""

import argparse
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

from campaign_context_fixture import configuration
from campaign_context_fixture.support import Owner, environment
from campaign_packet_fixture.sources import roots, text_profile
from postgres_fixture import owned_state

ROOT = Path(__file__).absolute().parents[1]


def verify(args):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1'
    output, installation = args.output.absolute(), args.installation.absolute()
    output.mkdir(parents=True, exist_ok=False)
    proof = json.loads((installation / 'manifest.json').read_bytes())
    assert proof['status'] == 'passed' and proof['planning'] == '0.67.0' and proof['scope'] == 'compiler'
    python = installation / 'environment/Scripts/python.exe'
    tests = output / 'tests/service'
    shutil.copytree(installation / 'tests/service', tests)
    shutil.copyfile(ROOT / 'services/agent_planning/tests/acceptance/test_declaration_publication.py',
                    tests / 'acceptance/test_declaration_publication.py')
    data_python = args.data_python.absolute()
    env = environment()
    subprocess.run([str(data_python), '-I', '-c',
        "from importlib.metadata import version; assert version('amphora-data-artifacts') == '0.29.0'"],
        env=env, cwd=output, check=True, capture_output=True, timeout=20)
    state = owned_state()
    host, port = state['endpoint'].split(':')
    env['CTX_DATA_DB'] = URL.create('postgresql+psycopg', username='artifact_service', password=state['password'],
        host=host, port=int(port), database=state['database']).render_as_string(hide_password=False)
    env.update(CTX_TOKEN=secrets.token_hex(32), CTX_DENIED=secrets.token_hex(32), CTX_FOREIGN=secrets.token_hex(32))
    scope = {'tenant_id': 'declaration-publication', 'project_id': uuid.uuid4().hex}
    storage = output / 'bytes'
    storage.mkdir()
    config = configuration.write(output / 'data.json', {
        'database_url_env': 'CTX_DATA_DB', 'storage_root': str(storage), 'profiles': [text_profile()],
        'acquisition': True, 'representations': False,
        'principals': configuration.principals(scope,
            ['upload', 'finalize', 'read', 'acquire', 'source_history', 'manage_source_rights'], ['upload'])})
    owner, results, pids, artifacts = None, [], [], None
    try:
        for stage in ('initial', 'replacement'):
            owner = Owner(data_python, 'amphora_data_artifacts', config, env, env['CTX_TOKEN'], output)
            pids.append(owner.process.pid)
            if artifacts is None:
                artifacts = roots(owner, scope)
            case = configuration.write(output / (stage + '.json'), {'stage': stage, 'scope': scope, 'roots': artifacts})
            result_path = output / (stage + '-result.json')
            worker = dict(environment(), CTX_TOKEN=env['CTX_TOKEN'], DECLARATION_CASE=str(case),
                          DECLARATION_RESULT=str(result_path), DECLARATION_DATA=owner.endpoint)
            result = subprocess.run([str(python), '-I', '-m', 'pytest',
                str(tests / 'acceptance/test_declaration_publication.py'),
                '--import-mode=importlib', '--tb=short', '-q', '--junitxml=' + str(output / (stage + '.xml'))],
                env=worker, cwd=output, capture_output=True, text=True, encoding='utf-8', timeout=90,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            (output / (stage + '.log')).write_text(result.stdout + result.stderr)
            assert result.returncode == 0, 'Declaration integration failed; inspect stage log'
            results.append(json.loads(result_path.read_bytes()))
            owner.close()
            owner = None
        assert results[0] == results[1]
    finally:
        if owner is not None:
            owner.close()
    configuration.write(output / 'manifest.json', {
        'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'planning': '0.67.0', 'data': '0.29.0', 'stages': 2, 'data_processes': pids,
        'result': results[0], 'limits': ['Retained Data PostgreSQL/public HTTP; no migration or reset',
            'Isolated Planning workers; deterministic synthetic provider output, no live model or scientific claim',
            'Exact publication and original preparation/review after owner restart; no compiler dispatch or active campaign repin']})
    print(json.dumps({'status': 'passed', 'stages': 2}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('installation', 'output', 'data-python'):
        parser.add_argument('--' + name, type=Path, required=True)
    verify(parser.parse_args())
