"""Tool-owned bounded input carriers; existing population records stay unchanged."""
import hashlib
import json
from typing import Annotated,Literal

from pydantic import Field
from amphora_contracts_core import ArtifactRef,Digest,Identifier,SchemaRef,WireModel
from amphora_contracts_population import (AbsentProcessInput,MaterialUse,ProcessBinding,
    MaterialMappingItem,MaterialMappingPolicy,ProcessContext)


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


class TransformMaterialsRequest(WireModel):
    schema_version: Literal["1"]
    profile: Literal["synthetic-transform-materials-v1"]
    policy: Literal["copy-first-representation-v1"]
    context: ProcessContext
    binding: ProcessBinding
    inputs: Annotated[tuple[MaterialUse,...],Field(min_length=1,max_length=32)]
    absent: Annotated[tuple[AbsentProcessInput,...],Field(max_length=32)]
    conditions: ArtifactRef
    output_count: Annotated[int,Field(ge=1,le=32)]


class ProcessAttemptLocator(WireModel):
    """Known attempt address only; deliberately carries no acceptance/completion ID."""
    activation_id: Digest
    invocation_id: Identifier
    attempt_id: Identifier
    fence: Annotated[int,Field(ge=1,le=9007199254740991)]


class ProposedProcessTransform(WireModel):
    schema_version: Literal["1"]
    profile: Literal["synthetic-process-transform-result-v1"]
    context: ProcessContext
    request: ArtifactRef
    source: ProcessAttemptLocator
    outputs: Annotated[tuple[MaterialUse,...],Field(min_length=1,max_length=32)]


class DeriveProcessRequest(WireModel):
    schema_version: Literal["1"]
    profile: Literal["synthetic-derive-process-v1"]
    result: ArtifactRef


class DerivedMaterialBatch(WireModel):
    schema_version: Literal["1"]
    profile: Literal["synthetic-derived-material-batch-v1"]
    context: ProcessContext
    derivation: ArtifactRef
    collection: ArtifactRef


def payload_schema(model,name):
    schema=model.model_json_schema(mode="validation")
    schema.update({"$schema":"https://json-schema.org/draft/2020-12/schema",
        "$id":f"urn:amphora:{name}:1:validation"})
    return (json.dumps(schema,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)+"\n").encode()


def schema_ref(model,name):
    return SchemaRef(schema_id=name,version="1",sha256=hashlib.sha256(payload_schema(model,name)).hexdigest())
