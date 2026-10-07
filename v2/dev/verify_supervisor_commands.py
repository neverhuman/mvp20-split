"""Selected-host CLI process proof with a dedicated invalid Registry configuration."""

from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from amphora_deployment.lifecycle import ProcessJob


def verify():
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    output = Path(sys.argv[1] if len(sys.argv) > 1 else '.test-results/supervisor-commands-20261006a').absolute()
    output.mkdir(parents=True, exist_ok=False)
    configuration = output / 'registry.json'
    configuration.write_text('{}', encoding='utf-8')
    manifest = output / 'manifest.json'
    manifest.write_text(json.dumps({'profile':'local-supervisor-v1','owners':{'registry':{
        'installation':str(Path('.test-results/local-owner-inventory-20261006a/owners/registry').absolute()),
        'source_lock':str(Path('v2/services/capability_registry/uv.lock').absolute()),
        'configuration':str(configuration), 'secret_references':[]}}}), encoding='utf-8')
    command = [sys.executable, '-I', '-m', 'amphora_deployment.lifecycle']
    def control(action, owner=False):
        result = subprocess.run([*command, action, '--root', str(root), *(['--owner','registry'] if owner else [])],
                                capture_output=True, text=True, timeout=35, creationflags=subprocess.CREATE_NO_WINDOW)
        return result.returncode, json.loads(result.stdout)
    with ProcessJob() as job:
        supervisor = subprocess.Popen([*command, 'serve', '--root', str(root), '--manifest', str(manifest)],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        job.attach(supervisor)
        try:
            deadline = time.monotonic() + 30
            while True:
                code, status = control('status')
                if code == 0:
                    break
                if supervisor.poll() is not None:
                    diagnostic = json.loads(supervisor.stdout.read())
                    if diagnostic.get('reason') == 'deployment_operation_busy':
                        print('Observed deployment operation lock contention during supervisor startup.')
                    raise AssertionError('supervisor exited before control readiness')
                assert time.monotonic() < deadline
                time.sleep(.1)
            assert status['owners']['registry']['state'] == 'not_started'
            code, first = control('start', True)
            assert code == 0
            deadline = time.monotonic() + 30
            while True:
                code, status = control('status')
                state = status['owners']['registry']
                if state['state'] == 'exited':
                    break
                assert time.monotonic() < deadline
            assert state['exit_code'] == 2 and state['readiness'] == 'not_assessed'
            code, repeated = control('start', True)
            assert code == 0 and repeated['pid'] == first['pid']
            code, restarted = control('restart', True)
            assert code == 0
            code, stopped = control('force-stop', True)
            assert code == 0 and stopped['state'] == 'exited'
            assert control('shutdown')[0] == 0
            assert supervisor.wait(timeout=15) == 0
        finally:
            if supervisor.poll() is None:
                supervisor.terminate()
            supervisor.wait(timeout=15)
            supervisor.stdout.close()
    result = {'checked_at':datetime.now().astimezone().isoformat(timespec='seconds'),
              'status':'passed', 'first':first, 'repeated':repeated, 'restarted':restarted,
              'stopped':stopped, 'supervisor_exit':0,
              'limits':'Registry config intentionally invalid; successful serving/migrations and graceful drain remain B2. No application-ready claim.'}
    (output / 'evidence.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Actual supervisor CLI start/status/restart/force-stop/shutdown passed:',output / 'evidence.json')


if __name__ == '__main__':
    try:
        verify()
    except Exception:
        raise SystemExit('Supervisor command verification failed; raw diagnostics suppressed.') from None
