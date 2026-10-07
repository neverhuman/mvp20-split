"""Actual Linux tool/container ownership under lost create/start replies; synthetic HTTP only."""

import argparse
import http.server
import json
import threading
import time
from datetime import datetime
from pathlib import Path

from amphora_deployment.persistence.state import LocalState
from amphora_deployment.profile import ProfileError
from amphora_deployment.scientific_workers.engine import ContainerEngine
from amphora_deployment.scientific_workers.journal import ContainerJournal
from amphora_deployment.scientific_workers.profiles import ToolProfile
from amphora_deployment.scientific_workers.turn import ContainerTurn
from amphora_deployment.tool_access import TLSIdentity
from amphora_deployment.tool_access.managed import AccessBinding, AccessGroup
from amphora_deployment.tool_access.proxy import OwnerRoute


def verify(output, bundle, identity_directory, image_id):
    output.mkdir(parents=True, exist_ok=False)
    bundle.mkdir(parents=True, exist_ok=False)
    identity = TLSIdentity.load(identity_directory)
    entered, release = threading.Event(), threading.Event()
    observed_requests = []
    class Owner(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get('Content-Length', '0'))
            assert 0 < length <= 65536
            self.rfile.read(length)
            observed_requests.append(self.path)
            entered.set()
            assert release.wait(15)
            self.send_response(503)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'{}')

        def log_message(self, *_):
            pass
    upstream = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Owner)
    thread = threading.Thread(target=upstream.serve_forever)
    thread.start()
    access = AccessGroup({name: AccessBinding(identity, OwnerRoute(name, upstream.server_port), 0)
                          for name in ('runtime', 'artifact')})
    certificate = bundle / 'certificate.pem'
    certificate.write_bytes(identity.certificate.read_bytes())
    cases = []
    try:
        ports = {name: access.start(name)['port'] for name in ('runtime', 'artifact')}
        with LocalState(bundle / 'controller') as state:
            for variant in ('lost_create', 'lost_start'):
                entered.clear()
                release.clear()
                observed_requests.clear()
                configuration = bundle / (variant + '.json')
                configuration.write_text(json.dumps({'actor_id': 'synthetic-worker',
                    'scope': {'tenant_id': 'engineering', 'project_id': 'container-lifecycle'},
                    'run_id': 'no-campaign-admitted', 'image_sha256': image_id[7:],
                    'runtime': {'endpoint': 'https://host.docker.internal:' + str(ports['runtime']),
                                'token_env': 'AMPHORA_RUNTIME_TOKEN'},
                    'artifacts': {'endpoint': 'https://host.docker.internal:' + str(ports['artifact']),
                                  'token_env': 'AMPHORA_ARTIFACT_TOKEN'}}))
                profile = ToolProfile.pin('evolution-seed', image_id, configuration, certificate,
                                          ports['runtime'], ports['artifact'])
                journal = ContainerJournal(bundle / (variant + '-turn.json'), state.identity, profile.name, profile.fingerprint)
                calls = []
                class Engine(ContainerEngine):
                    lose = True
                    def __init__(self, selected, operations):
                        self.variant, self.calls = selected, operations

                    def create(self, *args):
                        result = super().create(*args)
                        self.calls.append('create')
                        if self.variant == 'lost_create' and self.lose:
                            self.lose = False
                            raise ProfileError('simulated_lost_create_reply')
                        return result

                    def start(self, *args):
                        result = super().start(*args)
                        self.calls.append('start')
                        if self.variant == 'lost_start' and self.lose:
                            self.lose = False
                            raise ProfileError('simulated_lost_start_reply')
                        return result
                engine = Engine(variant, calls)
                environment = {'AMPHORA_RUNTIME_TOKEN': 'synthetic-runtime-token-00000000000000000',
                               'AMPHORA_ARTIFACT_TOKEN': 'synthetic-artifact-token-0000000000000000'}
                turn = ContainerTurn(journal, engine, profile, environment)
                try:
                    try:
                        turn.launch()
                        raise AssertionError('Required lost-reply case was not reached')
                    except ProfileError as error:
                        assert str(error) == 'simulated_' + variant + '_reply'
                    original = journal.read()['turn_id']
                    replacement = ContainerTurn(journal, engine, profile, environment)
                    replacement.launch()
                    assert entered.wait(10), 'Actual Linux tool did not reach TLS upstream'
                    assert replacement.poll() is None
                    container_id = journal.read()['container_id']
                    release.set()
                    deadline = time.monotonic() + 30
                    while replacement.poll() is None:
                        assert time.monotonic() < deadline
                        time.sleep(.2)
                    assert replacement.poll() == 3, 'Synthetic unavailable owner must reject the actual tool turn'
                    replacement.launch()
                    assert engine.observe(journal.read(), profile).status == 'exited'
                    assert calls == ['create', 'start'] and len(observed_requests) == 1
                    assert journal.read()['turn_id'] == original
                    replacement.release()
                    assert journal.read()['phase'] == 'released'
                    assert engine.observe(journal.read(), profile) is None
                    cases.append({'variant': variant, 'container_id': container_id, 'tool_exit_code': 3,
                                  'single_create_and_start': True, 'upstream_requests': 1,
                                  'same_turn_recovered': True, 'exited_container_removed_without_volumes': True})
                finally:
                    release.set()
                    record = journal.read()
                    if record is not None and record['phase'] != 'released':
                        observed = engine.observe(record, profile)
                        if observed is not None:
                            # Exact observed identity only; never names or volumes.
                            if observed.status == 'running':
                                engine._run('container', 'stop', '--time', '1', observed.container_id)
                            engine._run('container', 'rm', observed.container_id)
    finally:
        release.set()
        access.close()
        upstream.shutdown()
        upstream.server_close()
        thread.join(5)
    record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
        'image_id': image_id, 'cases': cases,
        'limits': ['Actual Linux evolution0.5/SDK0.2 through managed TLS; synthetic unavailable upstream',
                   'Controller reply loss injected after real Docker operations; no actual daemon outage',
                   'No owner eligibility, campaign, scientific result or model call',
                   'Responsive controller integration, startup adoption and migration guard remain subsequent work']}
    (output / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'cases': len(cases)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bundle-directory', type=Path, required=True)
    parser.add_argument('--identity-directory', type=Path, required=True)
    parser.add_argument('--image-id', required=True)
    args = parser.parse_args()
    verify(args.output.absolute(), args.bundle_directory.absolute(), args.identity_directory.absolute(), args.image_id)
