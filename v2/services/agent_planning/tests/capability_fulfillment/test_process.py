"""Configured production worker with scripted public HTTP owners and no model."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import sys
from threading import Thread

import pytest

from amphora_agent_planning.capability_requests.reader import CapabilityRequestReader
from amphora_agent_planning.capability_fulfillment.journal import FulfillmentJournal
from .test_verification import setup
from ..curation_worker.test_configuration import files

pytestmark = pytest.mark.postgres


@contextmanager
def peers(collector):
    state = {'unavailable': True, 'paths': []}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            state['paths'].append(self.path)
            assert self.headers.get('Authorization') == 'Bearer ' + 'x' * 40
            status, content, media = 200, b'', 'application/json'
            if state['unavailable']:
                status = 503
            elif self.path == '/v1/releases/' + collector.release.lock.descriptor_sha256:
                content = collector.release.model_dump_json().encode()
            else:
                for row in collector.processed:
                    path = '/v1/artifacts/' + row.reference.artifact_id
                    if self.path == path:
                        content = row.reference.model_dump_json().encode()
                        break
                    if self.path == path + '/processing-content':
                        content, media = row.body, row.reference.media_type
                        break
                else: status = 404
            self.send_response(status)
            self.send_header('Content-Type', media)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield 'http://127.0.0.1:' + str(server.server_port), state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_configured_replacement_resumes_pending_then_recovers_without_peer_rechecks(stored, tmp_path, monkeypatch):
    owner, principal, raw, first, identifier, collector = setup(stored)
    path, config, policy = files(tmp_path, monkeypatch)
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}: value.update(principal.scope.model_dump())
            if 'actor_id' in value: value['actor_id'] = principal.actor_id
            for item in value.values(): rescope(item)
        elif isinstance(value, list):
            for item in value: rescope(item)
    rescope(config)
    rescope(policy)
    (tmp_path / 'policy.json').write_text(json.dumps(policy), encoding='utf-8')
    monkeypatch.setenv('CURATION_TEST_DATABASE', stored.engine.url.render_as_string(hide_password=False))
    def run():
        result = subprocess.run([sys.executable, '-m', 'amphora_agent_planning.curation_worker', 'run',
            '--config', str(path), '--seconds', '0.1', '--interval', '0.05'], capture_output=True,
            text=True, timeout=45, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)
    with peers(collector) as (endpoint, state):
        config['data']['endpoint'] = config['registry']['endpoint'] = endpoint
        path.write_text(json.dumps(config), encoding='utf-8')
        assert run().get('fulfillment_pending') == 1
        assert CapabilityRequestReader(stored.engine).read(owner, first.specification.request.request_id).fulfillment == first
        state['unavailable'] = False
        assert run().get('fulfillment_verified') == 1
        paths = list(state['paths'])
        assert len(paths) == 4  # unavailable Registry, then exact Registry + metadata + processing.
        assert run().get('idle', 0) >= 1 and state['paths'] == paths
    result = CapabilityRequestReader(stored.engine).read(owner, first.specification.request.request_id)
    assert result.status == 'fulfilled' and result.fulfillment.status == 'verified'
    assert FulfillmentJournal(stored.engine).receive(owner, json.dumps(raw)) == first
    assert collector.calls == 0  # production public transports performed the verification.
