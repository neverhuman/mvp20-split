"""Public bounded population graph-step DTOs; no execution authority."""

import hashlib
import json
from functools import lru_cache

from amphora_contracts_core import SchemaRef

from .models import (
    SeedPopulationRequest, PreparedPopulationGeneration, PopulationSliceRequest, PopulationCandidateContext,
    PopulationMemberSlice, SelectPopulationRequest, ProposePopulationSuccessorRequest,
)

RECORDS = {
    "population-step.seed": SeedPopulationRequest,
    "population-step.prepared": PreparedPopulationGeneration,
    "population-step.slice-request": PopulationSliceRequest,
    "population-step.candidate-context": PopulationCandidateContext,
    "population-step.member-slice": PopulationMemberSlice,
    "population-step.select": SelectPopulationRequest,
    "population-step.successor": ProposePopulationSuccessorRequest,
}


@lru_cache(maxsize=7)
def population_step_schema(name):
    schema = RECORDS[name].model_json_schema(mode="validation")
    schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"urn:amphora:{name}:1:validation"})
    raw = (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    return SchemaRef(schema_id=name, version="1", sha256=hashlib.sha256(raw).hexdigest())
