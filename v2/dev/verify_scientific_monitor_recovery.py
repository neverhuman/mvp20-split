"""Kill an owned monitor process; adopt the same live Linux container without restarting it."""

import argparse
import http.server
import json
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from amphora_deployment.lifecycle import ProcessJob
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.profile import ProfileError
from amphora_deployment.scientific_workers.configuration import ScientificBinding
from amphora_deployment.scientific_workers.engine import ContainerEngine
from amphora_deployment.scientific_workers.monitor import ScientificSlot
from amphora_deployment.scientific_workers.ownership import require_released
from amphora_deployment.scientific_workers.profiles import ToolProfile
from amphora_deployment.tool_access import TLSIdentity
from amphora_deployment.tool_access.managed import AccessBinding, AccessGroup
from amphora_deployment.tool_access.proxy import OwnerRoute

IMAGE = 'sha256:7538bece7dceb2f6c395890abbc632fe58e188ba5120ef2d6ef070267809e878'
TOKENS = {'AMPHORA_RUNTIME_TOKEN': 'synthetic-runtime-token-00000000000000000',
          'AMPHORA_ARTIFACT_TOKEN': 'synthetic-artifact-token-0000000000000000'}


def binding_for(bundle, deployment_id):
    config = json.loads((bundle / 'worker.json').read_bytes())
    ports = [int(config[name]['endpoint'].rsplit(':', 1)[1]) for name in ('runtime', 'artifacts')]
    profile = ToolProfile.pin('evolution-seed', IMAGE, bundle / 'worker.json', bundle / 'certificate.pem', *ports)
    return ScientificBinding.pin(bundle / 'controller', deployment_id, profile, TOKENS)


def child(bundle):
    with LocalState(bundle / 'controller') as state:
        slot = ScientificSlot(binding_for(bundle, state.identity))
        print(json.dumps({'ready': True, 'status': slot.status()}), flush=True)
        try:
            for line in sys.stdin:
                action = line.strip()
                try:
                    if action == 'adopt':
                        slot.adopt()
                    elif action in {'start', 'quiesce', 'recover'}:
                        getattr(slot, action)()
                    elif action == 'exit':
                        slot.require_quiescent()
                        print(json.dumps({'closing': True}), flush=True)
                        break
                    elif action != 'status':
                        raise ValueError('Unsupported fixture command')
                    print(json.dumps({'status': slot.status()}), flush=True)
                except ProfileError as error:
                    print(json.dumps({'error': str(error)}), flush=True)
        finally:
            slot.detach()


class MonitorProcess:
    def __init__(self, bundle):
        self.job = ProcessJob()
        self.process = subprocess.Popen([sys.executable, '-I', str(Path(__file__).absolute()),
            'child', '--bundle-directory', str(bundle)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
        self.job.attach(self.process)
        self.messages = queue.Queue()
        self.reader = threading.Thread(target=self._read)
        self.reader.start()
        self.ready = self.messages.get(timeout=10)
        assert self.ready and self.ready.get('ready')

    def _read(self):
        for line in self.process.stdout:
            self.messages.put(json.loads(line))
        self.messages.put(None)

    def command(self, action):
        self.process.stdin.write(action + '\n')
        self.process.stdin.flush()
        result = self.messages.get(timeout=3)
        assert result is not None, 'Monitor process exited unexpectedly'
        return result

    def close(self):
        self.job.close()
        self.process.wait(timeout=10)
        self.reader.join(5)
        assert not self.reader.is_alive()
        self.process.stdin.close()
        self.process.stdout.close()


def verify(output, bundle, identity_directory, prepared_phase=None):
    output.mkdir(parents=True, exist_ok=False)
    bundle.mkdir(parents=True, exist_ok=False)
    identity = TLSIdentity.load(identity_directory)
    (bundle / 'certificate.pem').write_bytes(identity.certificate.read_bytes())
    entered, release = threading.Event(), threading.Event()
    requests = []
    class Owner(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            requests.append(self.path)
            entered.set()
            assert release.wait(20)
            self.send_response(503)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'{}')
        def log_message(self, *_):
            pass
    owner = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Owner)
    owner_thread = threading.Thread(target=owner.serve_forever)
    owner_thread.start()
    access = AccessGroup({name: AccessBinding(identity, OwnerRoute(name, owner.server_port), 0)
                          for name in ('runtime', 'artifact')})
    first = replacement = binding = None
    engine = ContainerEngine()
    try:
        ports = {name: access.start(name)['port'] for name in ('runtime', 'artifact')}
        config = {'actor_id': 'synthetic-worker', 'scope': {'tenant_id': 'engineering', 'project_id': 'monitor-recovery'},
            'run_id': 'no-campaign-admitted', 'image_sha256': IMAGE[7:],
            'runtime': {'endpoint': 'https://host.docker.internal:' + str(ports['runtime']), 'token_env': 'AMPHORA_RUNTIME_TOKEN'},
            'artifacts': {'endpoint': 'https://host.docker.internal:' + str(ports['artifact']), 'token_env': 'AMPHORA_ARTIFACT_TOKEN'}}
        (bundle / 'worker.json').write_text(json.dumps(config), encoding='utf-8')
        with LocalState(bundle / 'controller') as state:
            deployment_id = state.identity
        binding = binding_for(bundle, deployment_id)
        if prepared_phase is not None:
            assert prepared_phase in {'intent', 'created'}
            record = binding.journal.intent()
            if prepared_phase == 'created':
                container_id = engine.create(record, binding.profile, TOKENS)
                binding.journal.created(container_id)
        first = MonitorProcess(bundle)
        first.command('adopt' if prepared_phase is not None else 'start')
        assert entered.wait(10), 'Linux worker did not reach the held TLS fixture'
        original = binding.journal.read()
        observed = engine.observe(original, binding.profile)
        assert original['phase'] in {'starting', 'started'} and observed.status == 'running'
        first.close()  # Actual Windows job death, not graceful slot.detach.
        first = None
        assert engine.observe(binding.journal.read(), binding.profile).status == 'running'
        try:
            require_released(bundle / 'controller', deployment_id)
            raise AssertionError('Outstanding container did not block migration guard')
        except ProfileError as error:
            assert str(error) == 'migration_requires_reconciled_containers'
        replacement = MonitorProcess(bundle)
        assert replacement.ready['status']['state'] == 'quiescing'
        assert replacement.ready['status']['active_turn']
        replacement.command('adopt')
        started = time.monotonic()
        assert replacement.command('status')['status']['active_turn']
        control_seconds = time.monotonic() - started
        assert control_seconds < .5
        release.set()
        deadline = time.monotonic() + 30
        while True:
            status = replacement.command('status')['status']
            if status['completed_turns'] == 1:
                break
            assert time.monotonic() < deadline
            time.sleep(.1)
        assert status['exit_code'] == 3 and status['faulted'] and len(requests) == 1
        final = binding.journal.read()
        assert final['phase'] == 'released' and final['turn_id'] == original['turn_id']
        assert final['container_id'] == original['container_id'] and final['sequence'] == 1
        assert engine.observe(final, binding.profile) is None
        require_released(bundle / 'controller', deployment_id)
        recovered = replacement.command('recover')
        assert recovered['status']['state'] == 'quiescent'
        assert replacement.command('exit')['closing']
        assert replacement.process.wait(timeout=10) == 0
        record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
            'prepared_phase': prepared_phase,
            'image_id': IMAGE, 'container_id': original['container_id'], 'turn_id': original['turn_id'],
            'container_survived_monitor_job_death': True, 'startup_adoption_marked_active_before_observation': True,
            'single_original_upstream_request': True, 'journal_released_and_container_removed': True,
            'migration_guard_blocked_then_passed': True, 'status_latency_seconds': round(control_seconds, 4),
            'limits': ['Actual monitor process death/adoption with TLS fixture kept available in parent',
                       'Synthetic503 owner yields expected tool exit3; no campaign, model or scientific eligibility',
                       'Full controller/TLS death and daemon outage are distinct unproven cases']}
        (output / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': 'passed', 'same_container_adopted': True}), flush=True)
    finally:
        release.set()
        for process in (first, replacement):
            if process is not None:
                process.close()
        if binding is not None:
            retained = binding.journal.read()
            if retained is not None and retained['phase'] != 'released':
                observed = engine.observe(retained, binding.profile)
                if observed is not None:
                    if observed.status == 'running':
                        engine._run('container', 'stop', '--time', '1', observed.container_id)
                    engine._run('container', 'rm', observed.container_id)
        access.close()
        owner.shutdown()
        owner.server_close()
        owner_thread.join(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['verify', 'child'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--bundle-directory', type=Path, required=True)
    parser.add_argument('--identity-directory', type=Path)
    parser.add_argument('--prepared-phase', choices=['intent', 'created'])
    args = parser.parse_args()
    if args.action == 'child':
        child(args.bundle_directory.absolute())
    else:
        verify(args.output.absolute(), args.bundle_directory.absolute(), args.identity_directory.absolute(), args.prepared_phase)
