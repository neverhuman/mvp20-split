"""Actual loopback peer tests; durable dispatch eligibility belongs to the caller."""

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.supervision_client import (
    ExchangeAbsent,
    ExchangeConflict,
    ExchangeDenied,
    ExchangeInvalid,
    ExchangeUnavailable,
    ExchangeWindow,
    PlanningClient,
)

from ..supervision_responses.test_receipts import command_and_payload, receipt

TOKEN = 'synthetic-planning-client-token-00000000000000'


@pytest.fixture
def peer():
    command, payload = command_and_payload('planning.supervision.request')
    state = SimpleNamespace(command=command, payload=payload, receipt=receipt(command, payload),
        records=[], status=200, override=None, drop=False, slow=False, media='application/json')
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            self.respond(self.rfile.read(int(self.headers.get('Content-Length', '0'))))

        def do_GET(self):
            self.respond(None)

        def respond(self, body):
            state.records.append((self.command, self.path, body, self.headers.get('Authorization')))
            if state.drop:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            raw = (state.payload if self.command == 'GET' else state.receipt).model_dump_json().encode()
            if state.override is not None:
                raw = state.override
            self.send_response(state.status)
            self.send_header('Content-Type', state.media)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Location', 'http://127.0.0.1:1/no-redirect')
            self.end_headers()
            try:
                if state.slow:
                    for byte in raw:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(.03)
                else:
                    self.wfile.write(raw)
            except OSError:
                pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .02}, daemon=True)
    thread.start()
    state.endpoint = f'http://127.0.0.1:{server.server_port}'
    state.client = PlanningClient(command.identity.actor_id, command.identity.scope, state.endpoint, TOKEN)
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_separate_submit_receipt_readback_and_original_wire(peer):
    window = ExchangeWindow()
    checks = []
    saved = peer.client.submit(peer.command, window, guard=lambda: checks.append('guard'))
    assert checks == ['guard', 'guard'] and saved.status == 'awaiting_readback'
    observed = peer.client.receipt(peer.command, window, previous=saved)
    confirmed = peer.client.readback(peer.command, observed, window)
    assert confirmed.status == 'recorded'
    assert [record[:2] for record in peer.records] == [
        ('POST', '/v1/supervision/requests'), ('POST', '/v1/supervision/receipts/query'),
        ('GET', '/v1/supervision/requests/' + peer.payload.planning_request.reference.engagement_id)]
    assert peer.records[0][2] == peer.records[1][2] == peer.command.canonical_bytes
    assert all(record[3] == 'Bearer ' + TOKEN for record in peer.records)
    with pytest.raises(ValueError, match='call_limit'):
        peer.client.receipt(peer.command, window)


def test_lost_reply_never_reposts_and_original_receipt_can_be_recovered(peer):
    peer.drop = True
    with pytest.raises(ExchangeUnavailable, match='write_uncertain'):
        peer.client.submit(peer.command, ExchangeWindow(), guard=lambda: None)
    assert len(peer.records) == 1
    peer.drop = False
    observed = peer.client.receipt(peer.command, ExchangeWindow())
    assert peer.client.readback(peer.command, observed, ExchangeWindow()).status == 'recorded'
    assert sum(record[1] == '/v1/supervision/requests' for record in peer.records) == 1


@pytest.mark.parametrize('status,error', [(401, ExchangeDenied), (403, ExchangeDenied), (404, ExchangeAbsent),
                                        (409, ExchangeConflict), (422, ExchangeInvalid), (302, ExchangeUnavailable),
                                        (503, ExchangeUnavailable)])
def test_exact_read_failure_types_and_no_redirect_or_retry(peer, status, error):
    peer.status = status
    with pytest.raises(error):
        peer.client.receipt(peer.command, ExchangeWindow())
    assert len(peer.records) == 1


@pytest.mark.parametrize('mode', ['wrong-command', 'wrong-commit', 'duplicate', 'nonfinite', 'oversize', 'media'])
def test_untrusted_peer_data_never_becomes_a_verified_receipt(peer, mode):
    data = peer.receipt.model_dump(mode='json')
    if mode == 'wrong-command':
        data['outcome']['binding']['request_sha256'] = 'f' * 64
    elif mode == 'wrong-commit':
        data['outcome']['committed']['object_id'] = 'other'
    peer.override = json.dumps(data).encode()
    if mode == 'duplicate':
        peer.override = b'{"outcome":1,"outcome":2}'
    elif mode == 'nonfinite':
        peer.override = b'{"outcome":NaN}'
    elif mode == 'oversize':
        peer.override = b' ' * 262145
    elif mode == 'media':
        peer.media = 'text/html'
    with pytest.raises(ValueError):
        peer.client.submit(peer.command, ExchangeWindow(), guard=lambda: None)


def test_changed_owner_operation_and_readback_fail(peer):
    observed = peer.client.receipt(peer.command, ExchangeWindow())
    data = peer.receipt.model_dump(mode='json')
    data['outcome']['binding']['operation_id'] = 'different'
    peer.override = json.dumps(data).encode()
    with pytest.raises(ValueError, match='operation_changed'):
        peer.client.receipt(peer.command, ExchangeWindow(), previous=observed)
    peer.override = None
    peer.payload = peer.payload.model_copy(update={'checkpoint_id': 'wrong'})
    with pytest.raises(ValueError, match='readback_mismatch'):
        peer.client.readback(peer.command, observed, ExchangeWindow())


def test_guard_failure_and_actor_configuration_prevent_send(peer):
    def stale():
        raise ValueError('stale_fence')
    with pytest.raises(ValueError, match='stale_fence'):
        peer.client.submit(peer.command, ExchangeWindow(), guard=stale)
    with pytest.raises(ValueError, match='guard_required'):
        peer.client.submit(peer.command, ExchangeWindow(), guard=None)
    other = PlanningClient('other', peer.command.identity.scope, peer.endpoint, TOKEN)
    with pytest.raises(ValueError, match='client_authority'):
        other.receipt(peer.command, ExchangeWindow())
    assert not peer.records


def test_whole_sequence_deadline_bounds_trickled_receipt(peer):
    peer.slow = True
    started = time.monotonic()
    with pytest.raises(ExchangeUnavailable):
        peer.client.receipt(peer.command, ExchangeWindow(.15))
    assert time.monotonic() - started < 1.5 and len(peer.records) == 1


def test_invalid_configuration_and_total_budget(peer):
    for endpoint in ['http://example.com:80', 'http://127.0.0.1:bad', 'http://127.0.0.1:80/path']:
        with pytest.raises(ValueError, match='supervisor_endpoint'):
            PlanningClient(peer.command.identity.actor_id, peer.command.identity.scope, endpoint, TOKEN)
    with pytest.raises(ValueError, match='supervisor_credential'):
        PlanningClient(peer.command.identity.actor_id, peer.command.identity.scope, peer.endpoint, 'short')
    with pytest.raises(ValueError, match='supervisor_deadline'):
        ExchangeWindow(float('nan'))
    with pytest.raises(ExchangeUnavailable, match='total_bytes'):
        ExchangeWindow().consume(524289)
