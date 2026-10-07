"""One live turn per slot, explicit failure recovery and noninterrupting quiescence."""

import threading
import time

from ..profile import require


class WorkerSlot:
    """Binding launches a turn with poll()/release(); release never kills live work.

    tick is called by the owning controller, not a background scheduler. Successful
    turns repeat only while enabled. A failed or uncertain launch latches failure;
    recovery belongs to the binding and an explicit subsequent start.
    """

    def __init__(self, binding, *, interval=1, clock=time.monotonic):
        require(type(interval) in {int, float} and 0.05 <= interval <= 60, "worker_interval")
        self.binding, self.interval, self.clock = binding, interval, clock
        self.lock = threading.RLock()
        self.turn = None
        self.enabled = False
        self.failure = False
        self.exit_code = None
        self.completed_turns = 0
        self.next_turn = 0

    def _observe(self):
        if self.turn is None:
            return
        code = self.turn.poll()
        if code is None:
            return
        # Retain the handle on release failure: an uncertain cleanup cannot be
        # mistaken for a completed turn and followed by duplicate work.
        self.turn.release()
        self.turn = None
        self.exit_code = code
        self.completed_turns += 1
        self.next_turn = self.clock() + self.interval
        if code != 0:
            self.failure, self.enabled = True, False

    def _status(self):
        state = ("running" if self.enabled else "quiescing") if self.turn is not None else (
            "failed" if self.failure else "waiting" if self.enabled else "quiescent")
        return {"state": state, "exit_code": self.exit_code,
                "completed_turns": self.completed_turns, "faulted": self.failure,
                "execution_readiness": "not_assessed"}

    def _observe_safely(self):
        try:
            self._observe()
        except Exception:  # noqa: BLE001 - uncertain handles and private diagnostics stay local.
            self.failure, self.enabled = True, False

    def status(self):
        with self.lock:
            self._observe_safely()
            return self._status()

    def start(self):
        with self.lock:
            self._observe_safely()
            require(self.turn is None or self.enabled, "worker_requires_quiescence")
            require(not self.failure, "worker_requires_explicit_recovery")
            self.enabled = True
            return self._status()

    def recover(self):
        with self.lock:
            self._observe_safely()
            require(self.turn is None and not self.enabled, "worker_requires_quiescence")
            # Bindings must reconcile any external launch intent before allowing
            # another launch. Native turns use live job handles, never saved PIDs.
            self.binding.recover()
            self.failure = False
            return self._status()

    def quiesce(self):
        with self.lock:
            self.enabled = False
            self._observe_safely()
            return self._status()

    def tick(self):
        with self.lock:
            try:
                self._observe()
                if self.enabled and self.turn is None and self.clock() >= self.next_turn:
                    self.turn = self.binding.launch()
            except Exception:  # noqa: BLE001 - no retry after uncertain external effects.
                self.failure, self.enabled = True, False
                # Raw exceptions can include child configuration or credentials.
            return self._status()

    def require_quiescent(self):
        with self.lock:
            self._observe_safely()
            require(not self.enabled and self.turn is None and not self.failure,
                    "worker_requires_quiescence")

    def force_stop(self):
        with self.lock:
            self.enabled, self.failure = False, True
            if self.turn is not None:
                self.turn.force_stop()
                self._observe()
            return self._status()
