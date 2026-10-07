"""Repeatable process commands over fixed owner bindings; no execution authority."""

from dataclasses import dataclass, field
from pathlib import Path
import threading

from ..installation import SERVING_HOSTS
from ..profile import require
from .processes import OwnerProcess


@dataclass(frozen=True)
class OwnerBinding:
    installation: object
    directory: Path
    configuration: Path
    port: int
    environment: dict = field(repr=False)

    def launch(self, events):
        return OwnerProcess.start(self.installation, self.directory, self.configuration,
                                  self.port, self.environment, events)


class Supervisor:
    def __init__(self, bindings, events):
        require(set(bindings) <= set(SERVING_HOSTS) and bool(bindings), "lifecycle_bindings")
        self.bindings, self.events = dict(bindings), events
        self.processes = {}
        self.lock = threading.RLock()
        self.closed = False

    def status(self):
        with self.lock:
            return {owner: self.processes[owner].status() if owner in self.processes else {
                "owner": owner, "state": "not_started", "pid": None, "exit_code": None,
                "readiness": "not_assessed"} for owner in sorted(self.bindings)}

    def start(self, owner):
        with self.lock:
            require(not self.closed and owner in self.bindings, "lifecycle_owner_unavailable")
            if owner in self.processes:
                state = self.processes[owner].status()
                # Repeated start has no side effect, including after an unexpected exit.
                return state
            process = self.bindings[owner].launch(self.events)
            self.processes[owner] = process
            return process.status()

    def force_stop(self, owner):
        with self.lock:
            require(owner in self.bindings, "lifecycle_owner_unavailable")
            process = self.processes.get(owner)
            if process is not None:
                process.force_stop()
            return self.status()[owner]

    def drain(self, owner):
        with self.lock:
            require(owner in self.processes, "lifecycle_drain_requires_running")
            return self.processes[owner].drain()

    def restart(self, owner):
        with self.lock:
            require(not self.closed and owner in self.bindings, "lifecycle_owner_unavailable")
            process = self.processes.get(owner)
            require(process is None or process.status()["state"] == "exited", "lifecycle_restart_requires_stop")
            if process is not None:
                process.force_stop()
                del self.processes[owner]
            return self.start(owner)

    def close(self):
        with self.lock:
            # Normal control shutdown requires a completed drain/stop before this call.
            require(all(item.status()["state"] == "exited" for item in self.processes.values()), "lifecycle_shutdown_requires_stop")
            for process in self.processes.values():
                process.force_stop()
            self.closed = True
