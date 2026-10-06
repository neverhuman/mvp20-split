"""Current installed Runtime admission/checkpoint SQL crash and concurrency proof."""

import argparse
import ctypes
import json
import os
import shutil
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import URL, create_engine, text

from campaign_context_fixture.support import environment
from check_boundaries import ROOT
from postgres_fixture import owned_state


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def alive(pid):
    if os.name == 'nt':
        kernel = ctypes.windll.kernel32
        kernel.OpenProcess.restype = ctypes.c_void_p
        handle = kernel.OpenProcess(0x100000, False, pid)
        if not handle:
            return False
        try:
            return kernel.WaitForSingleObject(ctypes.c_void_p(handle), 0) == 258
        finally:
            kernel.CloseHandle(ctypes.c_void_p(handle))
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def verify(output, installation):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1', 'Explicit retained PostgreSQL opt-in required'
    output, installation = output.absolute(), installation.absolute()
    proof = json.loads((installation / 'manifest.json').read_bytes())
    assert proof['status'] == 'passed' and proof['owners']['runtime']['version'] == '0.40.0'
    output.mkdir(parents=True, exist_ok=False)
    root = output / 'root'
    shutil.copytree(installation / 'root', root, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    relative = Path('services/campaign_runtime/tests/supervision_checkpoints/process_worker.py')
    shutil.copyfile(ROOT / relative, root / relative)
    area = (root / relative).parent
    pythons = {label: installation / 'runtime' / label / 'Scripts/python.exe' for label in ('initial', 'replacement')}
    fixture = owned_state()
    host, port = fixture['endpoint'].split(':')
    url = URL.create('postgresql+psycopg', username='runtime_service', password=fixture['password'],
                     host=host, port=int(port), database=fixture['database'])
    inspector = create_engine(url.set(username='runtime_migrator'))
    try:
        with inspector.connect() as conn:
            assert conn.execute(text('SELECT version_num FROM runtime.alembic_version')).scalar_one() == 'runtime_0023'
    finally:
        inspector.dispose()
    state = output / 'state.json'
    write(state, {'scope': {'tenant_id': 'checkpoint-process-proof', 'project_id': uuid.uuid4().hex}})
    base = {**environment(), 'AMPHORA_CHECKPOINT_STATE': str(state),
            'AMPHORA_CHECKPOINT_SQL_URL': url.render_as_string(hide_password=False)}
    records, children = [], []

    def start(mode, label, name, gate=None):
        result = output / (name + '.json')
        env = {**base, 'AMPHORA_CHECKPOINT_MODE': mode, 'AMPHORA_CHECKPOINT_OUTPUT': str(result)}
        if gate is not None:
            env['AMPHORA_CHECKPOINT_GATE'] = str(gate)
        process = subprocess.Popen([str(pythons[label]), '-I', '-m', 'pytest', str(root / relative),
            '--confcutdir=' + str(area), '--import-mode=importlib', '-q', '--tb=short'],
            cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8',
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        children.append((process, result))
        return process, result

    def collect(process, result, expected=0):
        stdout, _ = process.communicate(timeout=120)
        with (output / 'process.log').open('a', encoding='utf-8') as stream:
            stream.write(stdout)
        assert process.returncode == expected, 'Installed checkpoint stage failed; inspect process.log'
        return json.loads(result.read_bytes())

    def stage(mode, label='replacement', code=0):
        process, result = start(mode, label, mode)
        value = collect(process, result, code)
        records.append({'mode': mode, 'installation': label, 'exit_code': code, 'result': value})
        print(json.dumps({'stage': mode, 'exit_code': code}), flush=True)
        return value

    def race(mode):
        gate = output / (mode + '.go')
        workers = [start(mode, label, mode + '-' + label, gate) for label in pythons]
        deadline = time.monotonic() + 60
        while not all(Path(str(path) + '.ready').exists() for _, path in workers):
            assert time.monotonic() < deadline and all(process.poll() is None for process, _ in workers), 'Race barrier failed'
            time.sleep(0.05)
        gate.write_text('go', encoding='utf-8')
        results = [collect(process, path) for process, path in workers]
        assert results[0] == results[1], 'Competing processes did not recover the exact same original'
        records.append({'mode': mode, 'workers': 2, 'barrier': 'both_ready_before_release', 'result': results[0]})
        print(json.dumps({'stage': mode, 'workers': 2, 'identical_original': True}), flush=True)
        return results[0]

    try:
        stage('initialize', 'initial')
        stage('kill_admission', 'initial', 91)
        stage('inspect_admission_rollback')
        admitted = race('admit')
        metadata = json.loads(state.read_bytes())
        metadata['run'] = admitted['run']
        write(state, metadata)
        assert stage('replay_admission') == admitted
        stage('kill_advance', 'initial', 92)
        stage('inspect_advance_rollback')
        advanced = race('advance')
        assert stage('fresh_advance')['checkpoint'] == advanced['checkpoint']
        stage('cancel')
        assert stage('terminal_replay') == advanced
    finally:
        for process, _ in children:
            if process.poll() is None:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True,
                        timeout=15, check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    process.kill()
                process.communicate(timeout=15)
        stage('cleanup')
    pids = sorted({process.pid for process, _ in children} |
        {int(Path(str(path) + '.pid').read_text()) for _, path in children if Path(str(path) + '.pid').exists()})
    assert not any(alive(pid) for pid in pids), 'Owned worker process remains alive'
    manifest = {'status': 'passed', 'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'runtime': '0.40.0', 'migration': 'runtime_0023', 'installations': 2, 'abrupt_exits': 2,
        'processes': len(children), 'checked_exited_pids': pids, 'records': records,
        'limits': ['Actual installed Runtime and PostgreSQL only; no SQL migration/reset',
                   'No provider, Planning request, accepted scalar effect or tool execution',
                   'Existing historical receipts, policy and checkpoint bytes retained after cancellation']}
    write(output / 'manifest.json', manifest)
    print(json.dumps({'status': 'passed', 'processes': len(children), 'abrupt_exits': 2}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--installation', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation)
