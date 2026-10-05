"""Public-protocol stubs with actual Planning SQL; not actual owner acceptance."""

import socket
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from amphora_agent_planning.campaign_authoring import AuthoringOutcome
from amphora_agent_planning.campaign_dispatch.dispatcher import CompilerDispatcher
from amphora_agent_planning.campaign_exchanges import (
    RegistryEligibilityClient,
    RuntimeAuthoringClient,
)
from sqlalchemy.exc import SQLAlchemyError

from ..campaign_authoring.test_values import receipt, saved, validation
from ..campaign_dispatch_coordinator.support import Registry, fixture


class ProtocolPeer:
    def __init__(self, stored, journal, lease, authoring):
        self.principal, self.journal, self.lease = stored.principal, journal, lease
        self.authoring = authoring
        self.operations, self.committed, self.calls, self.errors = {}, {}, [], []
        self.loss, self.denied, self.after_commit, self.valid = None, False, None, True
        self.registry = Registry(journal, stored.principal, lease)

    def register(self, operation):
        self.operations[operation.request.command().canonical_bytes if operation.effect.document().kind != 'resolve'
                        else operation.request.command.canonical_bytes] = operation

    def exchange(self, method, path, body):
        self.calls.append((method, path, body))
        if method == 'POST':
            operation = self.operations[body]
            kind = operation.effect.document().kind
            expected = '/v1/registry/resolve' if kind == 'resolve' else '/v1/definition-drafts/' + kind
            assert path == expected
            # Takes the same advisory transaction lock in a different connection.
            # A network call inside the dispatch transaction would time out here.
            retained = self.journal.read(self.principal, self.lease.selection.effect_id, operation.effect.effect_id)
            assert retained.progress.state == 'dispatching' and retained.effect == operation.effect
            if body not in self.committed:
                if kind == 'resolve':
                    value = self.registry.resolve('registry-fixture', operation.request.command, None, guard=lambda: None)
                elif kind == 'save':
                    value = saved(self.authoring)
                else:
                    value = AuthoringOutcome.bind(operation.request, receipt(operation.request),
                                                  validation(operation.request, valid=self.valid))
                self.committed[body] = value
            value = self.committed[body]
            if self.after_commit:
                self.after_commit()
            return 200, (value if kind == 'resolve' else value.receipt).model_dump_json().encode()
        assert method == 'GET' and not body
        if self.denied:
            return 403, b'{}'
        for value in self.committed.values():
            if not isinstance(value, AuthoringOutcome):
                continue
            command = value.request.command()
            receipt_path = '/v1/definition-commands/' + command.identity.command_family + '/' + command.identity.command_id
            commit = value.receipt.outcome.committed
            readback_path = ('/v1/definition-drafts/' + commit.object_id + '?revision=1'
                             if commit.kind == 'draft_revision' else '/v1/definition-validations/' + commit.object_id)
            if path == receipt_path:
                return 200, value.receipt.model_dump_json().encode()
            if path == readback_path:
                return 200, value.readback.model_dump_json().encode()
        return 404, b'{}'

    @property
    def posts(self):
        return [body for method, _, body in self.calls if method == 'POST']


@contextmanager
def hosted(stored, *, tools=False):
    store, journal, lease, _, refresh, runtime, _ = fixture(stored, tools=tools, maximum_age_seconds=60)
    peer = ProtocolPeer(stored, journal, lease, runtime.authoring)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def handle_request(self):
            self.connection.settimeout(5)
            try:
                assert self.headers.get('Authorization') == 'Bearer ' + 't' * 32
                length = int(self.headers.get('Content-Length', '0'))
                assert 0 <= length <= 1048576
                body = self.rfile.read(length)
                assert len(body) == length
                status, response = peer.exchange(self.command, self.path, body)
                if self.command == 'POST' and peer.loss == 'disconnect':
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.close_connection = True
                    return
                if self.command == 'POST' and peer.loss == 'malformed':
                    response = b'{'
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(response)))
                self.end_headers()
                self.wfile.write(response)
            except (AssertionError, KeyError, ValueError, OSError, SQLAlchemyError) as error:
                peer.errors.append(error)
                self.close_connection = True

        do_GET = do_POST = handle_request

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
    thread.start()
    endpoint = f'http://127.0.0.1:{server.server_port}'
    dispatcher = CompilerDispatcher(journal, refresh,
        RuntimeAuthoringClient('runtime', 'planning-agent', endpoint, 't' * 32),
        RegistryEligibilityClient('registry-fixture', 'planning-agent', endpoint, 't' * 32))
    try:
        yield store, journal, lease, dispatcher, refresh, peer
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)
        assert not thread.is_alive() and not peer.errors, peer.errors
