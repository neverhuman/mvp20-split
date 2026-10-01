"""Canonical records and ordered advisory locks shared inside the artifact owner."""

import hashlib
import json

from sqlalchemy import text

from ..acquisition.provenance import ProvenanceError

SCOPE = "tenant_id=:tenant AND project_id=:project"


def _canonical(record):
    body = json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(body) > 262144:
        raise ProvenanceError("record_limit")
    return body


def _lock(connection, scope, identities):
    keys = set()
    for identity in identities:
        raw = json.dumps([scope.tenant_id, scope.project_id, *identity], separators=(",", ":")).encode()
        keys.add(int.from_bytes(hashlib.sha256(raw).digest()[:8], "big", signed=True))
    for key in sorted(keys):
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})


