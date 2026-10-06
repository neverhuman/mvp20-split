"""Actual Runtime SQL and socket Planning peer; no actual Planning model worker."""

import socket
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.supervision_client import CheckpointPlanningClient
from amphora_campaign_runtime.supervision_delivery import RequestDispatcher
from amphora_campaign_runtime.supervision_journal.delivery import DeliveryJournal
from amphora_contracts_supervision import SupervisionCommandReceipt
from sqlalchemy import text

from ..supervision_journal.test_checkpoint_storage import command, setup


@pytest.fixture
def fixture(graph_env):
    journal, frame = setup(graph_env)
    principal = graph_env.env.principal
    outgoing = command(frame)
    journal.prepare(principal, frame, outgoing.canonical_bytes)
    state = SimpleNamespace(records=[], saved=False, drop=False, lookup_status=None, get_status=200,
                            receipt_status='recorded', before_absent=None)

    def receipt():
        outcome = {'status': state.receipt_status, 'binding': {'identity': outgoing.identity,
            'request_sha256': outgoing.sha256, 'operation_id': 'original-operation'}}
        if state.receipt_status == 'recorded':
            outcome['committed'] = {'kind': 'request', 'object_id': frame.request.planning_request.reference.engagement_id,
                                    'revision': 1, 'content_sha256': frame.request_sha256}
        elif state.receipt_status == 'rejected':
            outcome['reason_code'] = 'fixture_denied'
        return SupervisionCommandReceipt.model_validate({'outcome': outcome}).model_dump_json().encode()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            state.records.append((self.path, body))
            assert body == outgoing.canonical_bytes
            if self.path.endswith('/receipts/query'):
                status = state.lookup_status or (200 if state.saved else 404)
                if status == 404 and state.before_absent is not None:
                    state.before_absent()
            else:
                assert self.path == '/v2/supervision/requests'
                state.saved = True
                if state.drop:
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                status = 200
            self.respond(status, receipt())

        def do_GET(self):
            state.records.append((self.path, None))
            self.respond(state.get_status, frame.request.model_dump_json().encode())

        def respond(self, status, body):
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .02}, daemon=True)
    thread.start()
    client = CheckpointPlanningClient('fixture', principal.scope, f'http://127.0.0.1:{server.server_port}',
                                      'synthetic-dispatch-token-00000000000')
    delivery = DeliveryJournal(journal)
    worker = RequestDispatcher(delivery, client)
    state.tick = lambda worker=worker, principal=principal: worker.run(principal, frame.request.reference, frame.request_sha256)
    state.worker, state.delivery, state.frame, state.principal = worker, delivery, frame, principal
    state.engine = graph_env.env.engine
    state.params = journal.params(principal, frame.request.reference.run_id, frame.request.reference.decision_id)
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()


def test_receipt_saved_before_readback_and_terminal_replay_has_no_peer(fixture):
    f = fixture
    first = f.tick()
    assert first.previous.status == 'awaiting_readback' and not first.terminal
    assert [path for path, _ in f.records] == ['/v2/supervision/receipts/query', '/v2/supervision/requests']
    replacement = RequestDispatcher(DeliveryJournal(f.delivery.requests), f.worker.client)
    final = f.tick(replacement)
    assert final.terminal and final.previous.status == 'recorded'
    count = len(f.records)
    reader = replace(f.principal, actions=frozenset({'read'}))
    assert f.tick(RequestDispatcher(f.delivery, None), reader) == final
    assert len(f.records) == count


def test_lost_write_reply_recovers_original_without_resubmission(fixture):
    f = fixture
    f.drop = True
    assert f.tick().events[-1].evidence.reason == 'delivery_peer_uncertain'
    f.drop = False
    assert f.tick().previous.status == 'awaiting_readback'
    assert f.tick().terminal
    assert sum(path == '/v2/supervision/requests' for path, _ in f.records) == 1


def test_known_pending_receipt_disappearing_never_allows_post(fixture):
    f = fixture
    f.receipt_status = 'pending'
    assert f.tick().previous.status == 'pending'
    f.lookup_status = 404
    uncertain = f.tick()
    assert uncertain.events[-1].kind == 'unknown' and uncertain.previous.status == 'pending'
    assert sum(path == '/v2/supervision/requests' for path, _ in f.records) == 1
    f.lookup_status, f.receipt_status = None, 'recorded'
    assert f.tick().previous.status == 'awaiting_readback'
    assert f.tick().terminal


def test_missing_readback_retains_receipt_and_resumes_get(fixture):
    f = fixture
    f.tick()
    f.get_status = 404
    assert f.tick().events[-1].evidence.reason == 'delivery_readback_absent'
    f.get_status = 200
    assert f.tick().terminal
    assert [path for path, _ in f.records[-2:]] == [
        '/v2/supervision/requests/' + f.frame.request.planning_request.reference.engagement_id] * 2


@pytest.mark.parametrize('status,reason', [(403, 'delivery_peer_denied'), (409, 'delivery_peer_conflict'),
                                        (422, 'delivery_peer_rejected'), (503, 'delivery_peer_uncertain')])
def test_bounded_closed_peer_failure_without_write(fixture, status, reason):
    f = fixture
    f.lookup_status = status
    assert f.tick().events[-1].evidence.reason == reason
    assert len(f.records) == 1 and not f.saved


def test_cancellation_between_receipt_lookup_and_write_blocks_submission(fixture):
    f = fixture
    def cancel():
        with f.engine.begin() as conn:
            conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE tenant_id=:tenant "
                'AND project_id=:project AND run_id=:run'), f.params)
    f.before_absent = cancel
    with pytest.raises(ValueError, match='run_not_running'):
        f.tick()
    assert not f.saved and len(f.records) == 1


def test_contention_wrong_client_and_rejected_receipt(fixture):
    f = fixture
    with pytest.raises(ValueError, match='delivery_client_authority'):
        f.tick(RequestDispatcher(f.delivery, None))
    lease = f.delivery.claim(f.principal, f.frame.request.reference, f.frame.request_sha256, event_id='other')
    assert f.tick().events[-1].kind == 'claim' and not f.records
    f.delivery.observe(f.principal, lease, event_id='release', reason='fixture_release')
    with pytest.raises(ValueError, match='delivery_lease_lost'):
        f.delivery.guard(f.principal, lease)
    f.receipt_status = 'rejected'
    assert f.tick().terminal
    with f.engine.connect() as conn:
        assert conn.execute(text('SELECT status FROM runtime.runs WHERE tenant_id=:tenant '
            'AND project_id=:project AND run_id=:run'), f.params).scalar_one() == 'running'
