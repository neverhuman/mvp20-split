"""Exact schema identity; semantic validation remains the consuming owner."""

import hashlib
import json
from functools import lru_cache

from amphora_contracts_core import SchemaRef

from .specification import PopulationSpecification
from .membership import MembershipManifest, MembershipPage


def _reference(model, name):
    schema = model.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"urn:amphora:{name}:1:validation"
    raw = (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()
    return SchemaRef(schema_id=name, version="1", sha256=hashlib.sha256(raw).hexdigest())


@lru_cache(maxsize=1)
def population_specification_schema():
    return _reference(PopulationSpecification, "population.specification")


@lru_cache(maxsize=1)
def membership_page_schema():
    return _reference(MembershipPage, "population.membership-page")


@lru_cache(maxsize=1)
def membership_manifest_schema():
    return _reference(MembershipManifest, "population.membership-manifest")
