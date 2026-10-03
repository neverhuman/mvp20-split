"""Exact published validation schema identity for retained vector documents."""

import hashlib
import json

from amphora_contracts_core import SchemaRef

from .bindings import RepresentationVector


def representation_vector_schema():
    schema = RepresentationVector.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "urn:amphora:representations.vector:1:validation"
    raw = (
        json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")
    return SchemaRef(schema_id="representations.vector", version="1", sha256=hashlib.sha256(raw).hexdigest())
