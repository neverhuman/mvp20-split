"""Wall-clock timing helpers emitting `wall_seconds` into diagnostics dicts.

Usage:
    diag = {}
    with stopwatch(diag, "cluster_bootstrap"):
        ...work...
    # diag["cluster_bootstrap"]["wall_seconds"] -> float

    @timed(diag, "fit")
    def fit(...): ...
    # after each call: diag["fit"]["wall_seconds"] (last call),
    #                  diag["fit"]["calls"], diag["fit"]["total_wall_seconds"]

Timing values are measurement metadata: keep them OUT of canonical (two-replay
byte-stable) diagnostics; put them in a sidecar timing dict/file.
"""
import functools
import time
from contextlib import contextmanager

__all__ = ["stopwatch", "timed"]


@contextmanager
def stopwatch(diagnostics, key):
    """Context manager writing diagnostics[key]["wall_seconds"]."""
    t0 = time.perf_counter()
    try:
        yield
    finally:
        slot = diagnostics.setdefault(key, {})
        slot["wall_seconds"] = time.perf_counter() - t0


def timed(diagnostics, key=None):
    """Decorator factory; records per-call and cumulative wall_seconds."""
    def deco(fn):
        k = key or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                dt = time.perf_counter() - t0
                slot = diagnostics.setdefault(k, {})
                slot["wall_seconds"] = dt
                slot["calls"] = slot.get("calls", 0) + 1
                slot["total_wall_seconds"] = slot.get("total_wall_seconds", 0.0) + dt
        return wrapper
    return deco
