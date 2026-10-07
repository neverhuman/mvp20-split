"""One background monitor per scientific slot; control reads cached state only."""

import threading

from ..profile import require


class ScientificSlot:
    def __init__(self, binding):
        self.binding = binding
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.thread = None
        self.enabled = False
        self.standby_enabled = False
        self.active = self._pending()
        self.faulted = False
        self.closing = False
        self.completed = 0
        self.exit_code = None

    def _pending(self):
        record = self.binding.journal.read()
        return record is not None and record['phase'] in {'starting', 'started', 'exited'}

    def _spawn(self):
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._monitor, name='amphora-scientific-turn')
            try:
                self.thread.start()
            except BaseException:
                self.thread = None
                self.enabled, self.faulted = False, True
                raise

    def adopt(self):
        with self.lock:
            require(not self.closing, 'container_monitor_closed')
            if self.active:
                self._spawn()

    def start(self):
        with self.lock:
            require(not self.closing and not self.faulted, 'container_requires_recovery')
            require(not self.active or self.enabled, 'container_requires_quiescence')
            self.enabled, self.standby_enabled = True, False
            self._spawn()
            return self.status()

    def standby(self):
        with self.lock:
            require(not self.closing and not self.faulted and not self.active and not self.enabled,
                    'container_standby_requires_idle')
            self.standby_enabled = True
            return self.status()

    def offers_capacity(self):
        with self.lock:
            return ((self.standby_enabled or self.enabled) and not self.active
                    and not self.faulted and not self.closing)

    def quiesce(self):
        with self.lock:
            self.enabled, self.standby_enabled = False, False
            return self.status()

    def recover(self):
        with self.lock:
            require(not self.closing and not self.enabled and
                    (self.thread is None or not self.thread.is_alive()), 'container_recovery_requires_idle_monitor')
            self.active = self._pending()
            self.faulted = False
            if self.active:
                self._spawn()
            return self.status()

    def _monitor(self):
        try:
            while not self.stop.is_set():
                with self.lock:
                    if self.closing or (not self.active and not self.enabled):
                        return
                    launch = not self.active
                    self.active = True  # Accepted turn includes its create/start operations.
                turn = self.binding.turn()
                if launch:
                    turn.launch()
                while not self.stop.is_set():
                    code = turn.poll()
                    if code is not None:
                        break
                    self.stop.wait(.25)
                else:
                    return  # Detach leaves original pending journal/container for adoption.
                turn.release()
                with self.lock:
                    self.active = False
                    self.exit_code = code
                    self.completed += 1
                    if code != 0:
                        self.faulted, self.enabled = True, False
                        return
                self.stop.wait(1)
        except Exception:  # noqa: BLE001 - private Docker/configuration errors never enter status.
            with self.lock:
                self.enabled, self.faulted = False, True

    def status(self):
        with self.lock:
            return {'state': 'failed' if self.faulted else 'quiescing' if self.active and not self.enabled else
                    'running' if self.active else 'waiting' if self.enabled else
                    'standby' if self.standby_enabled else 'quiescent',
                    'active_turn': self.active, 'faulted': self.faulted, 'completed_turns': self.completed,
                    'exit_code': self.exit_code, 'execution_readiness': 'not_assessed'}

    def require_quiescent(self):
        with self.lock:
            require(not self.enabled and not self.standby_enabled and not self.active and not self.faulted,
                    'container_requires_quiescence')

    def detach(self):
        with self.lock:
            self.closing, self.enabled, self.standby_enabled = True, False, False
            self.stop.set()
            thread = self.thread
        if thread is not None:
            thread.join(60)
            require(not thread.is_alive(), 'container_monitor_detach_incomplete')
