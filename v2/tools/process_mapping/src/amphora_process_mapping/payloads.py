"""Tool-owned bounded input carriers; existing population records stay unchanged."""
import hashlib
import json
from typing import Annotated,Literal

from pydantic import Field
from amphora_contracts_core import ArtifactRef,SchemaRef,WireModel
from amphora_contracts_population import MaterialMappingItem,MaterialMappingPolicy,ProcessContext


class MaterialCollection(WireModel):
    schema_version: Literal["1"]
    profile: Literal["synthetic-material-collection-v1"]
    context: ProcessContext
    items: Annotated[tuple[MaterialMappingItem,...],Field(max_length=32)]


class MapMaterialsRequest(WireModel):
    schema_version: Literal["1"]
    profile: Literal["synthetic-map-materials-v1"]
    context: ProcessContext
    policy: MaterialMappingPolicy
    left: ArtifactRef
    right: ArtifactRef


def payload_schema(model,name):
    schema=model.model_json_schema(mode="validation")
    schema.update({"$schema":"https://json-schema.org/draft/2020-12/schema",
        "$id":f"urn:amphora:{name}:1:validation"})
    return (json.dumps(schema,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)+"\n").encode()


def schema_ref(model,name):
    return SchemaRef(schema_id=name,version="1",sha256=hashlib.sha256(payload_schema(model,name)).hexdigest())
