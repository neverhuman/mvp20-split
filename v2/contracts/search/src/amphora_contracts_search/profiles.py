"""Exact published validation-schema identities for public tool ports."""

import hashlib
import json

from amphora_contracts_core import SchemaRef

from .candidates import EvaluationObservation, EvaluationRequest
from .checkpoint import SearchCheckpoint
from .specification import SearchSpec


def _reference(model, name):
    schema = model.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"urn:amphora:{name}:1:validation"
    raw = (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()
    return SchemaRef(schema_id=name, version="1", sha256=hashlib.sha256(raw).hexdigest())


def search_spec_schema():
    return _reference(SearchSpec, "search.specification")


def search_checkpoint_schema():
    return _reference(SearchCheckpoint, "search.checkpoint")


def evaluation_request_schema():
    return _reference(EvaluationRequest, "search.evaluation-request")


def evaluation_observation_schema():
    return _reference(EvaluationObservation, "search.evaluation-observation")
