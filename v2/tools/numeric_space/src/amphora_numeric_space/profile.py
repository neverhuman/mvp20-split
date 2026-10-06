"""Versioned synthetic semantics; no source resolution or scientific authority."""

import hashlib
import json

from amphora_contracts_core import SchemaRef


def canonical(record):
    return json.dumps(
        record.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def pin(name, rules):
    body = json.dumps(
        {"profile": name, "version": "1", "rules": rules},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return SchemaRef(
        schema_id=name, version="1", sha256=hashlib.sha256(body).hexdigest()
    )


PROFILE = pin(
    "synthetic-numeric-space",
    "finite unique ordered coordinates; nonblank units; lower<=value<=upper; set one coordinate; preserve all other fields",
)
OPERATOR = pin(
    "synthetic-numeric-move",
    "single proposed move under the exact source profile; no repair, authorization or hidden iteration",
)
