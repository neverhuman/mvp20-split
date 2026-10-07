"""Controller-owned TLS listener lifetime; workers must quiesce before drain."""

import threading
from dataclasses import dataclass

from ..profile import require
from .identity import TLSIdentity
from .proxy import OwnerRoute, ToolAccessServer


@dataclass(frozen=True)
class AccessBinding:
    identity: TLSIdentity
    route: OwnerRoute
    port: int

    def launch(self):
        require(TLSIdentity.load(self.identity.directory) == self.identity, 'tool_tls_identity_changed')
        return AccessListener(ToolAccessServer(self.identity, self.route, port=self.port))


class AccessListener:
    def __init__(self, server):
        self.server = server
        self.draining = False
        self.failed = False
        self.thread = threading.Thread(target=self._serve, name='amphora-tool-tls')
        self.drain_thread = None
        try:
            self.thread.start()
        except BaseException:
            server.server_close()
            raise

    def _serve(self):
        try:
            self.server.serve_forever(poll_interval=.1)
        except Exception:  # noqa: BLE001 - no TLS/socket diagnostics enter control output.
            self.failed = True
        finally:
            if not self.draining:
                self.failed = True
            self.server.server_close()

    def status(self):
        alive = self.thread.is_alive()
        return {'state': 'failed' if self.failed else 'draining' if alive and self.draining else
                'running' if alive else 'drained', 'port': self.server.server_port,
                'upstream_readiness': 'not_assessed'}

    def drain(self):
        if self.drain_thread is None and self.thread.is_alive():
            self.draining = True
            self.drain_thread = threading.Thread(target=self.server.shutdown, name='amphora-tool-tls-drain')
            try:
                self.drain_thread.start()
            except BaseException:
                self.drain_thread = None
                self.failed = True
                raise
        return self.status()

    def require_stopped(self):
        require(not self.thread.is_alive(), 'tool_tls_requires_drain')
        if self.drain_thread is not None:
            self.drain_thread.join()

    def close(self):
        if self.thread.is_alive():
            self.draining = True
            self.server.shutdown()
        # Handshake <=5s plus absolute HTTP <=30s; never call a live listener drained.
        self.thread.join(40)
        self.require_stopped()


class AccessGroup:
    def __init__(self, bindings):
        require(type(bindings) is dict and set(bindings) <= {'runtime', 'artifact'}, 'tool_tls_bindings')
        self.bindings, self.listeners = dict(bindings), {}

    def status(self):
        return {name: self.listeners[name].status() if name in self.listeners else {'state': 'not_started'}
                for name in self.bindings}

    def start(self, name):
        require(name in self.bindings, 'tool_tls_owner')
        if name not in self.listeners:
            self.listeners[name] = self.bindings[name].launch()
        return self.listeners[name].status()

    def drain(self, name):
        require(name in self.listeners, 'tool_tls_requires_start')
        return self.listeners[name].drain()

    def restart(self, name):
        require(name in self.bindings, 'tool_tls_owner')
        if name in self.listeners:
            self.listeners[name].require_stopped()
            del self.listeners[name]
        return self.start(name)

    def require_running(self):
        require(all(row['state'] == 'running' for row in self.status().values()), 'tool_tls_requires_running')

    def require_stopped(self):
        for listener in self.listeners.values():
            listener.require_stopped()

    def close(self):
        for listener in self.listeners.values():
            try:
                listener.drain()
            except Exception:  # noqa: BLE001, S110 - synchronous close below retries cleanup without leaking diagnostics.
                pass
        failed = False
        for listener in self.listeners.values():
            try:
                listener.close()
            except Exception:  # noqa: BLE001 - attempt every listener before reporting safe aggregate failure.
                failed = True
        require(not failed, 'tool_tls_cleanup_incomplete')
