"""Actual loopback probes; scripted replies do not prove owner acceptance."""

import json
import threading
import time
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from amphora_agent_planning.campaign_exchanges import (
    CompilerWindow,
    ExchangeAbsent,
    ExchangeConflict,
    ExchangeDenied,
    ExchangeInvalid,
    ExchangeUnavailable,
    RegistryEligibilityClient,
    RuntimeAuthoringClient,
)
from amphora_contracts_tools import RegistryReceipt, parse_registry_command

from ..campaign_authoring.test_values import plan, receipt, saved, validation
from ..registry_access.test_discovery import record


@pytest.fixture(scope='module')
def authoring():
    return plan()


@pytest.fixture
def peer():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def handle_request(self):
            body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
            self.server.calls.append((self.command, self.path, self.headers.get('Authorization'), body))
            try:
                if self.server.slow == 'headers':
                    self.connection.sendall(b'HTTP/1.1 200 OK\r\nX-Slow: ')
                    for _ in range(30):
                        self.connection.sendall(b'x')
                        time.sleep(0.02)
                    return
                self.send_response(self.server.status)
                self.send_header('Content-Type', self.server.media)
                self.send_header('Content-Length', str(len(self.server.body)))
                self.end_headers()
                if self.server.slow == 'body':
                    for byte in self.server.body:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.02)
                else:
                    self.wfile.write(self.server.body)
            except OSError:
                pass

        do_POST = do_GET = handle_request

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    server.calls, server.status, server.media, server.body, server.slow = [], 200, 'application/json', b'{}', None
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
    thread.start()
    client = RuntimeAuthoringClient('runtime-fixture', 'planning-agent', f'http://127.0.0.1:{server.server_port}', 't' * 32)
    yield server, client
    server.shutdown()
    server.server_close()
    thread.join(2)


def test_runtime_save_receipt_and_exact_readback_routes(peer, authoring):
    server, client = peer
    request = authoring.save()
    server.body = receipt(request).model_dump_json().encode()
    window, fences = CompilerWindow('runtime'), []
    outcome = client.submit(request, window, guard=lambda: fences.append('checked'))
    assert outcome.status == 'awaiting_readback' and fences == ['checked', 'checked']
    assert client.receipt(request, window) == outcome
    server.body = saved(authoring).readback.model_dump_json().encode()
    assert client.readback(outcome, window).status == 'saved'
    assert [call[0] for call in server.calls] == ['POST', 'GET', 'GET']
    assert server.calls[0][1] == '/v1/definition-drafts/save'
    assert server.calls[0][2:] == ('Bearer ' + 't' * 32, request.canonical)
    assert server.calls[1][1].endswith(request.command().identity.command_id)
    assert server.calls[2][1].endswith(request.payload().draft_id + '?revision=1')
    assert window.calls == 3


def test_runtime_validation_preserves_invalid_compilation(peer, authoring):
    server, client = peer
    request = authoring.validate(saved(authoring))
    server.body = receipt(request).model_dump_json().encode()
    window = CompilerWindow('runtime')
    outcome = client.submit(request, window, guard=lambda: None)
    server.body = validation(request, valid=False).model_dump_json().encode()
    assert client.readback(outcome, window).status == 'structural_invalid'
    assert [call[1] for call in server.calls] == ['/v1/definition-drafts/validate', '/v1/definition-validations/validation-1']


@pytest.mark.parametrize(('write', 'status', 'error'), [
    (True, 401, ExchangeDenied), (False, 403, ExchangeDenied),
    (False, 404, ExchangeAbsent), (True, 404, ExchangeUnavailable),
    (True, 409, ExchangeConflict), (False, 409, ExchangeConflict),
    (True, 400, ExchangeInvalid), (True, 413, ExchangeInvalid), (True, 415, ExchangeInvalid),
    (True, 422, ExchangeInvalid), (True, 500, ExchangeUnavailable), (False, 500, ExchangeUnavailable),
    (True, 302, ExchangeUnavailable),
])
def test_http_failures_are_distinct_and_never_retried(peer, authoring, write, status, error):
    server, client = peer
    server.status, server.body = status, b'private peer detail'
    request = authoring.save()
    with pytest.raises(error) as caught:
        if write:
            client.submit(request, CompilerWindow('runtime'), guard=lambda: None)
        else:
            client.receipt(request, CompilerWindow('runtime'))
    assert 'private' not in str(caught.value) and len(server.calls) == 1


@pytest.mark.parametrize('body', [b'{', b'NaN', b'{"a":1,"a":2}', b'\xff', b'x' * 262145],
                         ids=['malformed', 'nonfinite', 'duplicate', 'encoding', 'oversize'])
def test_invalid_or_oversized_response_never_becomes_acknowledgement(peer, authoring, body):
    server, client = peer
    server.body = body
    with pytest.raises(ValueError, match='compiler_response_protocol|compiler_response_limit'):
        client.submit(authoring.save(), CompilerWindow('runtime'), guard=lambda: None)
    assert len(server.calls) == 1


@pytest.mark.parametrize('stage', [1, 2])
def test_fence_loss_prevents_send(peer, authoring, stage):
    server, client = peer
    calls = []
    def guard():
        calls.append(1)
        if len(calls) == stage:
            raise ValueError('fence_lost')
    with pytest.raises(ValueError, match='fence_lost'):
        client.submit(authoring.save(), CompilerWindow('runtime'), guard=guard)
    assert not server.calls


@pytest.mark.parametrize('slow', ['headers', 'body'])
def test_whole_sequence_deadline_bounds_trickled_responses(peer, authoring, slow):
    server, client = peer
    request = authoring.save()
    server.slow, server.body = slow, receipt(request).model_dump_json().encode()
    started = time.monotonic()
    with pytest.raises(ExchangeUnavailable):
        client.submit(request, CompilerWindow('runtime', seconds=0.15), guard=lambda: None)
    assert time.monotonic() - started < 1.5
    assert len(server.calls) == 1


def test_owner_window_and_required_guard_reject_before_network(peer, authoring):
    server, client = peer
    request = authoring.save()
    with pytest.raises(ValueError, match='compiler_owner_binding'):
        client.submit(replace(request, owner_id='foreign'), CompilerWindow('runtime'), guard=lambda: None)
    with pytest.raises(ValueError, match='compiler_window_owner'):
        client.submit(request, CompilerWindow('registry'), guard=lambda: None)
    with pytest.raises(ValueError, match='compiler_write_guard_required'):
        client.submit(request, CompilerWindow('runtime'), guard=None)
    assert not server.calls


def test_call_and_aggregate_limits_are_per_sequence():
    for owner, count in [('runtime', 8), ('registry', 64)]:
        window = CompilerWindow(owner)
        for _ in range(count):
            window.start()
        with pytest.raises(ValueError, match='compiler_call_limit'):
            window.start()
    window = CompilerWindow('runtime')
    window.consume(16777216)
    with pytest.raises(ValueError, match='compiler_total_bytes'):
        window.consume(1)


def registry_command():
    release = record()
    return parse_registry_command('registry.resolve', json.dumps({
        'identity': {'scope': release.scope.model_dump(mode='json'), 'actor_id': 'planning-agent',
                     'command_family': 'registry.resolve', 'command_id': 'eligibility-1'},
        'payload': {'release': release.lock.model_dump(mode='json'), 'context': 'synthetic-tests',
                    'inputs': [port.model_dump(mode='json') for port in release.descriptor.tool.inputs],
                    'outputs': [port.model_dump(mode='json') for port in release.descriptor.tool.outputs]}}))


def test_registry_resolve_is_observation_transport_not_a_reservation(peer):
    server, _ = peer
    client = RegistryEligibilityClient('registry-fixture', 'planning-agent', f'http://127.0.0.1:{server.server_port}', 't' * 32)
    expected = RegistryReceipt(operation_id='registry-operation', status='rejected', reason_code='no_capacity',
                               release=None, deployment=None, heartbeat=None, decision=None)
    server.body = expected.model_dump_json().encode()
    command = registry_command()
    result = client.resolve('registry-fixture', command, CompilerWindow('registry'), guard=lambda: None)
    assert result == expected
    assert server.calls[0][1] == '/v1/registry/resolve' and server.calls[0][3] == command.canonical_bytes
    with pytest.raises(ValueError, match='compiler_owner_binding'):
        client.resolve('foreign', command, CompilerWindow('registry'), guard=lambda: None)
    assert len(server.calls) == 1


@pytest.mark.parametrize('endpoint', ['https://127.0.0.1:1234', 'http://localhost:1234', 'http://127.0.0.1',
                                    'http://127.0.0.1:1234/path', 'http://secret@127.0.0.1:1234',
                                    'http://127.0.0.1:1234?query=x', 'http://127.0.0.1:99999'])
def test_only_configured_loopback_origin_is_supported(endpoint):
    with pytest.raises(ValueError, match='compiler_endpoint'):
        RuntimeAuthoringClient('runtime', 'actor', endpoint, 't' * 32)


@pytest.mark.parametrize('seconds', [0, 21, float('nan'), float('inf'), True])
def test_window_rejects_invalid_deadline(seconds):
    with pytest.raises(ValueError, match='compiler_deadline'):
        CompilerWindow('runtime', seconds=seconds)


def test_media_and_foreign_receipt_do_not_become_acceptance(peer, authoring):
    server, client = peer
    request = authoring.save()
    server.media = 'text/html'
    with pytest.raises(ExchangeUnavailable, match='compiler_response_media'):
        client.submit(request, CompilerWindow('runtime'), guard=lambda: None)
    server.media = 'application/json'
    value = receipt(request).model_dump(mode='json')
    value['outcome']['binding']['request_sha256'] = 'f' * 64
    server.body = json.dumps(value).encode()
    with pytest.raises(ValueError, match='authoring_receipt_binding'):
        client.submit(request, CompilerWindow('runtime'), guard=lambda: None)
    assert len(server.calls) == 2


def test_registry_client_cannot_revoke_or_activate_a_tool(peer):
    server, _ = peer
    client = RegistryEligibilityClient('registry', 'planning-agent', f'http://127.0.0.1:{server.server_port}', 't' * 32)
    command = registry_command()
    value = json.loads(command.canonical_bytes)
    value['identity']['command_family'] = 'registry.revoke'
    value['payload'] = {'release': value['payload']['release'], 'expected_revision': 1}
    revoke = parse_registry_command('registry.revoke', json.dumps(value))
    with pytest.raises(ValueError):
        client.resolve('registry', revoke, CompilerWindow('registry'), guard=lambda: None)
    assert not server.calls
