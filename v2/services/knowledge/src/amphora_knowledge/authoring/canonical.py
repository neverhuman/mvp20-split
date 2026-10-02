"""Owner record fingerprints; distinct from the runtime command encoding profiles."""

import hashlib
import json


class KnowledgeError(ValueError):
    """Bounded stable code; never include authored source text in diagnostics."""


def canonical(record):
    return json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(record):
    return hashlib.sha256(canonical(record)).hexdigest()
