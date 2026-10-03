"""Bounded canonical generation identities, independent of storage and backend clients."""

import hashlib
import json

from ..representations.validation import digest, identifier, record

MAX_MANIFEST_BYTES = 4 * 1024 * 1024


class RetrievalError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise RetrievalError(code)


def canonical(value):
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    require(0 < len(raw) <= MAX_MANIFEST_BYTES, "retrieval_manifest_bound")
    return raw


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


__all__ = ["RetrievalError", "require", "canonical", "fingerprint", "digest", "identifier", "record"]
