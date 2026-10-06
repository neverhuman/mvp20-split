"""Attempt accounting and conservative paired reporting."""

from dataclasses import dataclass, field
from math import isfinite


@dataclass
class AttemptLedger:
    limit: int
    rows: list = field(default_factory=list)

    def begin(self, request_sha256):
        if len(self.rows) >= self.limit:
            raise ValueError("comparison_attempt_budget")
        self.rows.append({"attempt": len(self.rows) + 1, "request_sha256": request_sha256,
                          "status": "pending", "cost": None, "reason": None})
        return len(self.rows) - 1

    def finish(self, index, *, cost=None, reason=None):
        row = self.rows[index]
        if row["status"] != "pending":
            raise ValueError("comparison_attempt_already_terminal")
        if (cost is None) == (reason is None):
            raise ValueError("comparison_outcome")
        if cost is not None and (type(cost) not in {int, float} or not isfinite(cost)):
            raise ValueError("comparison_finite_cost")
        row.update(status="failed" if reason else "evaluated", cost=cost, reason=reason)

    def report(self, stop_reason, *, transport_error=None):
        best, prefixes = None, []
        for row in self.rows:
            if row["status"] == "evaluated":
                best = row["cost"] if best is None else min(best, row["cost"])
            prefixes.append(best)
        return {"allowance": self.limit, "attempts": len(self.rows),
                "failures": sum(r["status"] != "evaluated" for r in self.rows),
                "best_successful_cost": best,
                "mean_prefix_best_cost": (sum(prefixes) / len(prefixes)
                                          if prefixes and None not in prefixes else None),
                "stop_reason": stop_reason, "transport_error": transport_error,
                "rows": self.rows.copy()}


def compare(evolution, baseline):
    full = all(r["attempts"] == r["allowance"] and not r["failures"]
               and not r["transport_error"] and r["best_successful_cost"] is not None
               for r in (evolution, baseline))
    full = full and evolution["allowance"] == baseline["allowance"]
    delta = baseline["best_successful_cost"] - evolution["best_successful_cost"] if full else None
    return {"status": "complete" if full else "incomplete", "baseline_minus_evolution": delta,
            "outcome": ("incomplete" if delta is None else "gain" if delta > 0
                        else "loss" if delta < 0 else "tie")}
