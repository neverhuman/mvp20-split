"""Owner-approved actual Docker Desktop outage; exact baseline and tool intent recovery."""

import argparse
import http.server
import json
import subprocess
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from amphora_deployment.persistence.state import LocalState
from amphora_deployment.scientific_workers.engine import ContainerEngine
from amphora_deployment.scientific_workers.ownership import require_released
from amphora_deployment.tool_access import TLSIdentity
from amphora_deployment.tool_access.managed import AccessBinding, AccessGroup
from amphora_deployment.tool_access.proxy import OwnerRoute

from local_numeric_configuration import write
from verify_scientific_monitor_recovery import IMAGE, MonitorProcess, binding_for

APPROVED = {
    'amphora-local-7be3465bdf1e4fa6b9189637e51e6f96-qdrant',
    'amphora-local-7be3465bdf1e4fa6b9189637e51e6f96-postgres',
    'amphora-bp06-qdrant-a35053217a73404281489c8f2972cf1f',
    'amphora-bp06-qdrant-61d44f881a884955b4d5e71913230b9d',
    'amphora-bp02-61fe242e94ae4de7bb9c6d676e95cdaa',
}
FORMAT = ('{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Image}},'
          '"running":{{json .State.Running}},"mounts":{{json .Mounts}},'
          '"ports":{{json .HostConfig.PortBindings}}}')


def docker(*args, timeout=10, check=True):
    result = subprocess.run(['docker', *args], capture_output=True, text=True, encoding='utf-8',
        timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    if check:
        assert result.returncode == 0, 'Docker operation failed: ' + ' '.join(args[:2])
    return result


def inventory():
    ids = docker('ps', '-q', '--no-trunc').stdout.split()
    return [json.loads(docker('inspect', identifier, '--format', FORMAT).stdout) for identifier in sorted(ids)]


def restore(baseline, output, *, start=True):
    print('Restoring Docker Desktop and exact original container IDs', flush=True)
    if start:
        docker('desktop', 'start', '--timeout', '120', timeout=130)
    deadline = time.monotonic() + 120
    while docker('info', '--format', '{{.OSType}}', check=False).returncode:
        assert time.monotonic() < deadline, 'Docker engine did not return'
        time.sleep(2)
    for original in baseline:
        current = json.loads(docker('inspect', original['id'], '--format', FORMAT).stdout)
        assert {k: v for k, v in current.items() if k != 'running'} == {k: v for k, v in original.items() if k != 'running'}
        if not current['running']:
            docker('start', original['id'], timeout=20)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for original in baseline:
        deadline = time.monotonic() + 60
        while True:
            if 'qdrant' in original['name']:
                actual_ports = json.loads(docker('inspect', original['id'], '--format', '{{json .NetworkSettings.Ports}}').stdout)
                port = actual_ports['6333/tcp'][0]['HostPort']
                try:
                    with opener.open('http://127.0.0.1:' + port + '/readyz', timeout=3) as response:
                        ready = response.status == 200
                except OSError:
                    ready = False
            else:
                ready = docker('exec', original['id'], 'pg_isready', check=False).returncode == 0
            if ready:
                break
            assert time.monotonic() < deadline, 'Original database failed readiness: ' + original['name']
            time.sleep(1)
    after = inventory()
    assert after == baseline, 'Original running inventory changed'
    write(output / 'restored-inventory.json', after)
    print('All five original containers restored with unchanged IDs/images/mounts/requested bindings and ready databases', flush=True)


def verify(output, bundle, identity_directory, resume_from=None):
    output.mkdir(parents=True, exist_ok=False)
    baseline = json.loads((resume_from / 'original-inventory.json').read_bytes()) if resume_from else inventory()
    assert {row['name'].lstrip('/') for row in baseline} == APPROVED, 'Running inventory exceeds approved scope'
    write(output / 'original-inventory.json', baseline)
    write(output / 'thresholds.json', {'control_seconds': .5, 'docker_stop_seconds': 60,
        'docker_start_seconds': 120, 'scope': 'Owner explicitly approved all five baseline containers'})
    if resume_from is None:
        bundle.mkdir(parents=True, exist_ok=False)
    identity = TLSIdentity.load(identity_directory)
    if resume_from:
        assert (bundle / 'certificate.pem').read_bytes() == identity.certificate.read_bytes()
    else:
        (bundle / 'certificate.pem').write_bytes(identity.certificate.read_bytes())
    entered, release = threading.Event(), threading.Event()
    requests = []
    class Owner(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            requests.append(self.path)
            entered.set()
            release.wait(20)
            self.send_response(503)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'{}')
        def log_message(self, *_):
            pass
    owner = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Owner)
    thread = threading.Thread(target=owner.serve_forever)
    thread.start()
    existing = json.loads((bundle / 'worker.json').read_bytes()) if resume_from else None
    prior_ports = {name: int(existing[key]['endpoint'].rsplit(':', 1)[1]) for name, key in
                   [('runtime', 'runtime'), ('artifact', 'artifacts')]} if existing else {}
    access = AccessGroup({name: AccessBinding(identity, OwnerRoute(name, owner.server_port), prior_ports.get(name, 0))
                          for name in ('runtime', 'artifact')})
    monitor = None
    stopped, restored = False, False
    try:
        ports = {name: access.start(name)['port'] for name in ('runtime', 'artifact')}
        config = {'actor_id': 'synthetic-worker', 'scope': {'tenant_id': 'engineering', 'project_id': 'daemon-outage'},
            'run_id': 'no-campaign-admitted', 'image_sha256': IMAGE[7:],
            'runtime': {'endpoint': 'https://host.docker.internal:' + str(ports['runtime']), 'token_env': 'AMPHORA_RUNTIME_TOKEN'},
            'artifacts': {'endpoint': 'https://host.docker.internal:' + str(ports['artifact']), 'token_env': 'AMPHORA_ARTIFACT_TOKEN'}}
        if existing:
            assert config == existing, 'Original worker binding changed'
        else:
            write(bundle / 'worker.json', config)
        with LocalState(bundle / 'controller') as state:
            deployment_id = state.identity
        binding = binding_for(bundle, deployment_id)
        monitor = MonitorProcess(bundle)
        assert inventory() == baseline, 'Running inventory changed before approved outage'
        if resume_from:
            prior = json.loads((resume_from / 'outage.json').read_bytes())
            original, stop_seconds = prior['original_turn'], prior['stop_seconds']
            latencies = [prior['maximum_control_seconds']]
            assert binding.journal.read() == original, 'Original outage intent changed'
            write(output / 'outage.json', prior)
        else:
            print('Stopping Docker Desktop without force; owner APIs/workers already drained', flush=True)
            stopped = True  # Recovery is mandatory even if the CLI times out after stopping.
            started = time.monotonic()
            docker('desktop', 'stop', '--timeout', '60', timeout=70)
            stop_seconds = time.monotonic() - started
            assert docker('info', '--format', '{{.OSType}}', check=False).returncode != 0
            print('Actual daemon unavailable; exercising one managed intent and cached control', flush=True)
            assert 'error' not in monitor.command('start')
            deadline, latencies = time.monotonic() + 30, []
            while True:
                tick = time.monotonic()
                status = monitor.command('status')['status']
                latencies.append(time.monotonic() - tick)
                assert latencies[-1] < .5
                if status['faulted']:
                    break
                assert time.monotonic() < deadline
                time.sleep(.1)
            original = binding.journal.read()
            assert original['phase'] == 'intent' and original['sequence'] == 1 and original['container_id'] is None
            write(output / 'outage.json', {'original_turn': original, 'monitor': status,
                'stop_seconds': stop_seconds, 'maximum_control_seconds': max(latencies), 'daemon_unavailable': True})
        restore(baseline, output, start=resume_from is None)
        restored = True
        assert 'error' not in monitor.command('recover')
        assert 'error' not in monitor.command('start')
        assert entered.wait(30), 'Recovered Linux worker did not reach actual TLS fixture'
        monitor.command('quiesce')
        release.set()
        deadline = time.monotonic() + 30
        while True:
            status = monitor.command('status')['status']
            if not status['active_turn']:
                break
            assert time.monotonic() < deadline
            time.sleep(.1)
        final = binding.journal.read()
        assert final['phase'] == 'released' and final['turn_id'] == original['turn_id'] and final['sequence'] == 1
        assert final['exit_code'] == 3 and len(requests) == 1
        assert ContainerEngine().observe(final, binding.profile) is None
        require_released(bundle / 'controller', deployment_id)
        assert 'error' not in monitor.command('recover')
        assert inventory() == baseline
        write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'original_inventory': baseline, 'original_turn': original, 'final_turn': final,
            'maximum_control_seconds': max(latencies), 'stop_seconds': stop_seconds,
            'one_original_intent_one_container': True, 'fixture_requests': len(requests), 'provider_calls': 0,
            'limits': ['Actual Docker outage and actual Linux/TLS process with synthetic503 owner response',
                       'No active campaign during outage; retained actual campaign readback is a separate required step']})
        print('Shared daemon outage and original-intent recovery passed; baseline restored', flush=True)
    finally:
        try:
            if stopped and not restored:
                restore(baseline, output)
        finally:
            release.set()
            try:
                if monitor is not None:
                    monitor.close()
            finally:
                try:
                    access.close()
                finally:
                    owner.shutdown()
                    owner.server_close()
                    thread.join(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'bundle', 'identity-directory'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--approved-shared-outage', action='store_true', required=True)
    parser.add_argument('--resume-from', type=Path, help='Recover original outage intent without stopping Docker again')
    args = parser.parse_args()
    verify(*(getattr(args, name).absolute() for name in ('output', 'bundle', 'identity_directory')),
           resume_from=args.resume_from.absolute() if args.resume_from else None)
