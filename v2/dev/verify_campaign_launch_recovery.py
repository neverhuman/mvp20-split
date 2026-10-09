"""Installed coordinator process death after a fixture owner commits admission."""
import argparse
import http.server
import json
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from amphora_contracts_graph_runtime import parse_graph_command
from amphora_contracts_runtime import CommandReceipt
from amphora_deployment.campaign_launch.coordinator import LaunchCoordinator
from amphora_deployment.campaign_launch.intent import LaunchIntent
from amphora_deployment.campaign_launch.journal import LaunchJournal
from amphora_deployment.campaign_launch.runtime_peer import RuntimePeer
from amphora_deployment.lifecycle import ProcessJob
from amphora_deployment.persistence.state import LocalState

TOKEN = 'synthetic-launch-recovery-token'


def intent():
    identity = {'command_family': 'campaign.launch', 'command_id': 'launch-recovery',
        'actor_id': 'engineer', 'scope': {'tenant_id': 'engineering', 'project_id': 'launch-recovery'}}
    return LaunchIntent.parse(json.dumps({'encoding': 'amphora-command-v2', 'identity': identity,
        'payload': {'profile': {'profile_id': 'fixture', 'version': '1', 'sha256': 'd' * 64},
        'admission': {'identity': {**identity, 'command_family': 'graph.admit_draft'}, 'payload': {
            'plan_sha256': 'a' * 64, 'inputs': [], 'budget': {'limit': 8, 'max_attempts_per_activation': 2},
            'draft': {'draft_id': 'draft', 'revision': 1, 'content_sha256': 'b' * 64,
                'validation_id': 'validation', 'universe_sha256': 'c' * 64}}}}}).encode())


def child(root, port):
    with LocalState(root):
        journal = LaunchJournal(root / 'campaign-launches')
        journal.submit(intent(), lambda value: None)
        coordinator = LaunchCoordinator(journal, SimpleNamespace(check=lambda value: None),
            RuntimePeer(port, TOKEN), object())
        state = coordinator.tick()
        if state.phase == 'admission_unresolved':
            state = coordinator.tick()
        print(state.receipt().model_dump_json(), flush=True)


def verify(output):
    output.mkdir(parents=True, exist_ok=False)
    entered, release = threading.Event(), threading.Event()
    receipts, submissions = {}, []
    class Owner(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def respond(self, status, raw):
            self.send_response(status); self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw))); self.end_headers()
            try: self.wfile.write(raw)
            except OSError: pass
        def do_GET(self):
            assert self.headers['Authorization'] == 'Bearer ' + TOKEN
            assert self.path == '/v1/commands/graph.admit_draft/launch-recovery?actor_id=engineer'
            raw = receipts.get('receipt')
            self.respond(200 if raw else 404, raw or b'{"reason_code":"receipt_unavailable"}')
        def do_POST(self):
            assert self.path == '/v1/graph-runs/drafts'
            assert self.headers['Authorization'] == 'Bearer ' + TOKEN
            raw = self.rfile.read(int(self.headers['Content-Length']))
            command = parse_graph_command('graph.admit_draft', raw)
            submissions.append(raw)
            receipt = CommandReceipt.model_validate_json(json.dumps({'outcome': {'status': 'accepted',
                'binding': {'identity': command.identity.model_dump(), 'request_sha256': command.sha256,
                            'operation_id': 'fixture-operation'},
                'committed': {'kind': 'run', 'object_id': 'fixture-run', 'revision': 0}}}))
            receipts['receipt'] = receipt.model_dump_json().encode()
            entered.set()
            assert release.wait(15)
            self.respond(200, receipts['receipt'])
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Owner)
    thread = threading.Thread(target=server.serve_forever); thread.start()
    root = output / 'controller'
    command = [sys.executable, '-I', str(Path(__file__).absolute()), 'child', '--output', str(root), '--port', str(server.server_port)]
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    job, first = ProcessJob(), None
    try:
        first = subprocess.Popen(command, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        job.attach(first)
        assert entered.wait(10), 'Fixture owner did not observe admission'
        original = LaunchJournal(root / 'campaign-launches').active()
        assert original.phase == 'admission_unresolved'
        job.close(); first.wait(10)
        release.set()
        result = subprocess.run(command, env=environment, capture_output=True, text=True, encoding='utf-8', timeout=20,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert result.returncode == 0, 'Replacement coordinator failed'
        recovered = LaunchJournal(root / 'campaign-launches').active()
        assert recovered.run_id == 'fixture-run' and recovered.phase == 'admitted_not_engaged'
        assert recovered.intent.request.sha256 == original.intent.request.sha256
        assert submissions == [original.intent.admission.canonical_bytes]
        record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
            'process_death_after_owner_commit': True, 'same_request_sha256': recovered.intent.request.sha256,
            'same_admission_sha256': recovered.intent.admission.sha256, 'run_id': recovered.run_id,
            'admission_posts': len(submissions), 'original_receipt_recovered': True,
            'limits': ['Public HTTP owner is a deterministic fixture, not actual Runtime execution',
                'Installed coordinator/process lease/journal/transport exercised; no scientific or model calls']}
        (output / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': 'passed', 'admission_posts': 1}), flush=True)
    finally:
        release.set(); job.close()
        if first is not None: first.wait(10)
        server.shutdown(); server.server_close(); thread.join(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['verify', 'child'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', type=int)
    args = parser.parse_args()
    if args.action == 'child': child(args.output.absolute(), args.port)
    else: verify(args.output.absolute())
