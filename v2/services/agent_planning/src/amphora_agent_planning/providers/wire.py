"""Strict observation version selection; never reinterpret legacy journal bytes."""

import json

from amphora_contracts_planning import ProviderObservation, TaskProviderObservation

from ..context.policy import require
from ..context.snapshot import _constant, _object

OBSERVATION_LIMITS = {"1": 65536, "2": 262144}


def observation_document(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 262144, "observation_size")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("invalid_observation") from exc
    require(type(value) is dict, "invalid_observation")
    version = value.get("schema_version", "1")
    require(type(version) is str and version in OBSERVATION_LIMITS, "observation_version")
    require(len(raw) <= OBSERVATION_LIMITS[version], "observation_size")
    model = ProviderObservation if version == "1" else TaskProviderObservation
    return model.model_validate_json(json.dumps(value, allow_nan=False))
