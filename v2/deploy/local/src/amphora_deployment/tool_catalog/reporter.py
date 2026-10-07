"""One serialized background reporter per configured logical executor replica."""

import threading

from ..profile import require


class CapacityReporter:
    def __init__(self, probe, journal, transport):
        self.probe, self.journal, self.transport = probe, journal, transport
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.thread = None
        self.result = {'state': 'not_started', 'observation': None}

    def start(self):
        with self.lock:
            require(not self.stop.is_set(), 'catalog_reporter_closed')
            if self.thread is None:
                self.thread = threading.Thread(target=self._run, name='amphora-capacity-report')
                try:
                    self.thread.start()
                except BaseException:
                    self.thread = None
                    raise

    def _publish(self, state, observation=None):
        with self.lock:
            self.result = {'state': state, 'observation': observation}

    def _report(self, *, closing=False):
        try:
            observation = None if closing else self.probe.observe()
            ready = (not closing and observation.fresh() and self.probe.slot.offers_capacity()
                     and not self.stop.is_set())
            record = self.journal.read()
            if not ready and record['revision'] == 0 and record['pending'] is None:
                self._publish('unavailable')
                return  # No historical advertisement to withdraw; no speculative new command.
            command = self.journal.prepare(ready=ready)
            if command is None:
                self._publish('uncertain_waiting_for_fresh_readiness')
                return
            if command['payload']['free_slots'] and (self.stop.is_set() or not self.probe.slot.offers_capacity()
                                                      or not observation.fresh()):
                self._publish('uncertain_waiting_for_fresh_readiness')
                return
            received = self.transport.send(command)
            accepted = self.journal.accept(received)
            self._publish('observed', accepted)
        except Exception:  # noqa: BLE001 - retain original intent and never expose private transport errors.
            self._publish('delivery_or_observation_uncertain')

    def _run(self):
        while not self.stop.is_set():
            self._report()
            self.stop.wait(3)
        # Never manufacture withdrawal; last observation/uncertainty remains visible.
        self._report(closing=True)

    def quiesce(self):
        self.stop.set()

    def resume(self):
        with self.lock:
            if self.stop.is_set():
                require(self.thread is None or not self.thread.is_alive(), 'catalog_reporter_requires_drain')
                self.stop.clear()
                self.thread = None
        self.start()

    def status(self):
        with self.lock:
            return dict(self.result, running=self.thread is not None and self.thread.is_alive(),
                        stopping=self.stop.is_set())

    def require_stopped(self):
        require(self.thread is None or not self.thread.is_alive(), 'catalog_reporter_requires_drain')

    def close(self):
        self.quiesce()
        if self.thread is not None:
            self.thread.join(30)
        self.require_stopped()
