"""Bounded delivery passes; database transactions end before remote calls."""

import time

from .transport import DeliveryUnavailable


class DeliveryWorker:
    def __init__(self, store, targets):
        self.store, self.targets = store, targets

    def sweep(self, principal, *, limit=20, max_seconds=20):
        principal.require("deliver")
        if type(limit) is not int or not 1 <= limit <= 100 or not 0 < max_seconds <= 30:
            raise ValueError("Invalid delivery pass bounds")
        deadline = time.monotonic() + max_seconds
        totals = {"claimed": 0, "acknowledged": 0, "failed": 0, "stale": 0}
        while totals["claimed"] < limit and time.monotonic() < deadline:
            claims = self.store.claim(principal, limit=1)
            if not claims:
                break
            claim = claims[0]
            totals["claimed"] += 1
            try:
                self.targets.send(claim)
                acknowledged, reason = True, ""
            except DeliveryUnavailable as error:
                acknowledged, reason = False, str(error)
            except (ValueError, KeyError):
                acknowledged, reason = False, "invalid_delivery_payload"
            current = self.store.finish(principal, claim, acknowledged=acknowledged, reason=reason)
            totals["stale" if not current else "acknowledged" if acknowledged else "failed"] += 1
        return totals
