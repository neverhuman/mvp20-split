"""Periodic renewal of one exact job fence across bounded owner/provider calls."""
import math
from threading import Event, RLock, Thread
from ..context.policy import require


class LeaseKeeper:
    def __init__(self, jobs, principal, lease, *, interval_seconds=10, lease_seconds=60):
        require(type(lease_seconds) is int and 1 <= lease_seconds <= 60, 'curation_lease_bound')
        require(type(interval_seconds) in (int, float) and math.isfinite(interval_seconds)
                and 0 < interval_seconds <= lease_seconds / 3, 'curation_heartbeat_interval')
        self.jobs, self.principal, self.lease = jobs, principal, lease
        self.interval, self.seconds = interval_seconds, lease_seconds
        self.stop, self.lock, self.thread = Event(), RLock(), None
        self.failure = None

    def current(self):
        with self.lock:
            if self.failure is not None:
                raise ValueError(self.failure)
            self.lease = self.jobs.refresh(self.principal, self.lease, lease_seconds=self.seconds)
            return self.lease

    def _run(self):
        while not self.stop.wait(self.interval):
            try:
                if self.current().progress.terminal:
                    self.stop.set()
            except Exception as error:
                with self.lock:
                    self.failure = 'curation_lease_lost' if isinstance(error, ValueError) and str(error) == 'curation_lease_lost' else 'curation_heartbeat_unavailable'
                self.stop.set()

    def __enter__(self):
        require(self.thread is None, 'curation_heartbeat_already_started')
        self.current()
        self.thread = Thread(target=self._run, name='curation-heartbeat', daemon=True)
        self.thread.start()
        return self

    def __exit__(self, kind, value, traceback):
        self.stop.set()
        self.thread.join(15)
        require(not self.thread.is_alive(), 'curation_heartbeat_shutdown')
        self.jobs.release(self.principal, self.lease)
