"""Installed Runtime processes race/recover exact journal state; no peer/model calls."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import URL

from postgres_fixture import owned_state
from verify_runtime_scope import ROOT
from verify_runtime_scope import verify as verify_scope


def verify(output, predecessor):
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    verify_scope(output / 'initial', predecessor)
    initial_manifest = json.loads((output / 'initial/manifest.json').read_bytes())
    assert initial_manifest['runtime'] == '0.26.0'
    root = output / 'root'
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc')
    for relative in ('services/campaign_runtime/tests', 'contracts/supervision/tests/fixtures'):
        shutil.copytree(ROOT / relative, root / relative, ignore=ignore)
    fixture = Path('contracts/fixtures/v2/executable_cases.json')
    (root / fixture).parent.mkdir(parents=True)
    shutil.copyfile(ROOT / fixture, root / fixture)
    area = root / 'services/campaign_runtime/tests/supervision_journal'
    env = {key: value for key, value in os.environ.items() if not key.startswith('AMPHORA') and key != 'PYTHONPATH'}
    env['PYTHONUTF8'] = '1'

    def run(args, *, environment=env, expected=0, timeout=120):
        result = subprocess.run([str(arg) for arg in args], cwd=root, env=environment,
            capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        with (output / 'journal.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == expected, 'Installed journal stage failed; inspect journal.log'
        return result

    first = output / 'initial/environment/Scripts/python.exe'
    replacement = output / 'replacement'
    uv = ROOT / '.venv/Scripts/uv.exe'
    run([uv, 'venv', '--python', sys.executable, replacement])
    second = replacement / 'Scripts/python.exe'
    run([uv, 'pip', 'install', '--python', second, *sorted((output / 'initial/wheels').glob('*.whl')), 'pytest>=8,<9'])
    pure = []
    for label, python in (('initial', first), ('replacement', second)):
        report = output / (label + '-pure.xml')
        run([python, '-I', '-m', 'pytest', area / 'test_frames.py', area / 'test_series.py',
            '--confcutdir=' + str(area), '--import-mode=importlib', '-q', '--tb=short', '--junitxml=' + str(report)])
        suites = ET.parse(report).getroot().findall('testsuite')
        assert all(int(s.attrib[k]) == 0 for s in suites for k in ('errors', 'failures', 'skipped'))
        pure.append({'installation': label, 'tests': sum(int(s.attrib['tests']) for s in suites)})
        print(json.dumps({'installation': label, 'pure_journal_tests': pure[-1]['tests']}), flush=True)
    fixture_state = owned_state()
    host, port = fixture_state['endpoint'].split(':')
    url = URL.create('postgresql+psycopg', username='runtime_service', password=fixture_state['password'],
                     host=host, port=int(port), database=fixture_state['database'])
    migration_env = {**env, 'AMPHORA_RUNTIME_MIGRATION_URL': url.set(username='runtime_migrator').render_as_string(hide_password=False)}
    run([first, '-I', '-m', 'amphora_campaign_runtime.persistence.migrate'], environment=migration_env)
    state = output / 'probe-state.json'
    state.write_text(json.dumps({'scope': {'tenant_id': 'supervision-process-proof', 'project_id': uuid.uuid4().hex}}), encoding='utf-8')
    shared_env = {**env, 'AMPHORA_JOURNAL_PROBE_SQL_URL': url.render_as_string(hide_password=False),
                  'AMPHORA_JOURNAL_PROBE_STATE': str(state)}
    records = []
    worker = area / 'process_worker.py'

    def invocation(python, mode, label, barrier=None):
        result_path = output / (label + '.json')
        process_env = {**shared_env, 'AMPHORA_JOURNAL_PROBE_OUTPUT': str(result_path), 'AMPHORA_JOURNAL_PROBE_MODE': mode}
        if barrier is not None:
            process_env['AMPHORA_JOURNAL_PROBE_BARRIER'] = str(barrier)
        args = [str(python), '-I', '-m', 'pytest', str(worker), '--confcutdir=' + str(area),
                '--import-mode=importlib', '-q', '--tb=short']
        return args, process_env, result_path

    def stage(python, mode, *, code=0):
        args, process_env, result_path = invocation(python, mode, mode)
        run(args, environment=process_env, expected=code)
        record = json.loads(result_path.read_bytes())
        records.append({'mode': mode, 'installation': 'initial' if python == first else 'replacement',
                        'exit_code': code, 'result': record})
        print(json.dumps({'stage': mode, 'verified_exit': code}), flush=True)
        return record

    def race(mode):
        gate = output / (mode + '.go')
        children = []
        try:
            for label, python in (('a', first), ('b', second)):
                args, process_env, result_path = invocation(python, mode, mode + '-' + label, gate)
                children.append((subprocess.Popen(args, cwd=root, env=process_env, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, encoding='utf-8'), result_path))
            deadline = time.monotonic() + 40
            while not all(Path(str(path) + '.ready').exists() for _, path in children):
                assert time.monotonic() < deadline and all(p.poll() is None for p, _ in children), 'race barrier failed'
                time.sleep(0.05)
            gate.write_text('go', encoding='utf-8')
            results = []
            for process, path in children:
                stdout, _ = process.communicate(timeout=40)
                with (output / 'journal.log').open('a', encoding='utf-8') as stream:
                    stream.write(stdout)
                assert process.returncode == 0, 'race worker failed'
                results.append(json.loads(path.read_bytes()))
            records.append({'mode': mode, 'workers': 2, 'barrier': 'both_ready_before_release', 'results': results})
            print(json.dumps({'stage': mode, 'competing_workers': 2}), flush=True)
            return results
        finally:
            for process, _ in children:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=10)

    try:
        stage(first, 'initialize')
        stage(first, 'kill_prepare_before_commit', code=91)
        stage(second, 'inspect_empty')
        roots = race('prepare')
        assert roots[0] == roots[1], 'competing exact roots changed original bytes/timestamps'
        stage(second, 'changed_retry')
        members = race('successor_race')
        assert sorted(item['outcome'] for item in members) == ['conflict', 'recorded']
        claims = race('claim')
        assert sum(item['lease'] is not None for item in claims) == 1, 'multiple live lease winners'
        stage(first, 'kill_after_claim', code=93)
        recovered = stage(second, 'recover_delivery')
        assert all(recovered[key] == value for key, value in roots[0].items())
        stage(first, 'kill_response_before_commit', code=94)
        stage(second, 'inspect_response_pending')
        stage(first, 'kill_response_after_commit', code=95)
        stage(second, 'recover_response')
    finally:
        stage(second, 'cleanup')
    manifest = {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'runtime': '0.26.0', 'migration': 'runtime_0019', 'installations': 2,
        'scope_predecessor': initial_manifest, 'pure_journal': pure, 'process_records': records,
        'processes': sum(item.get('workers', 1) for item in records), 'abrupt_exits': 4,
        'limits': ['Actual installed Runtime/PostgreSQL only; outgoing Planning receipt is a deterministic public fixture',
                   'No HTTP peer, paid provider call, accepted graph decision or independently authored replacement']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'processes': manifest['processes'], 'abrupt_exits': 4}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--predecessor', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.predecessor)
