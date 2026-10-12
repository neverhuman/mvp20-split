"""Bounded fair polling; no paid retry, graph replacement, or hidden startup."""
import math
import time

from ..context.policy import require
from .discovery import CurationDiscovery


class CurationPoller:
    def __init__(self, worker, policy_ids, worker_id, *, fulfillments=None):
        self.worker, self.worker_id = worker, worker_id
        self.discovery = CurationDiscovery(worker.engine, policy_ids)
        self.fulfillments, self.fulfillment_turn = fulfillments, False

    def tick(self, principal):
        if self.fulfillments is not None:
            self.fulfillment_turn = not self.fulfillment_turn
            if self.fulfillment_turn:
                result = self.fulfillments.tick(principal)
                if result is not None:
                    return result
        identity = self.discovery.next(principal)
        if identity is not None:
            return self.worker.tick(principal, identity, self.worker_id)
        if self.fulfillments is not None and not self.fulfillment_turn:
            return self.fulfillments.tick(principal)
        return None

    def sweep(self, principal, *, seconds=20, interval=1, stop=None):
        require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= 86400
            and type(interval) in (int, float) and math.isfinite(interval) and 0.05 <= interval <= 60,
            'curation_polling_window')
        deadline, counts = time.monotonic() + seconds, {}
        while time.monotonic() < deadline and not (stop is not None and stop.is_set()):
            result = self.tick(principal)
            status = 'idle' if result is None else result.status
            counts[status] = counts.get(status, 0) + 1
            remaining = deadline - time.monotonic()
            if remaining > 0:
                delay = min(interval, remaining)
                if stop is None:
                    time.sleep(delay)
                else:
                    stop.wait(delay)
        return counts
