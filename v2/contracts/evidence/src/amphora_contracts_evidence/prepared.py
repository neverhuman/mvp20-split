"""Bounded fixture preparation outputs, never scientific acceptance records."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_core import SchemaRef, WireModel
from pydantic import Field

LabText = Annotated[str, Field(max_length=2048)]


class PreparedDocument(WireModel):
    wire_version: Literal["1"]
    text: Annotated[str, Field(max_length=4194304)]


class PreparedLabRecord(WireModel):
    wire_version: Literal["1"]
    candidate_id: LabText | None
    candidate_revision: LabText | None
    sample_id: LabText | None
    sample_revision: LabText | None
    method: LabText | None
    context: LabText | None
    value: LabText | None
    unit: LabText | None


def prepared_schema(profile: Literal["document", "lab"]) -> SchemaRef:
    """Digest the same validation schema bytes published by the contract exporter."""
    model, name = {"document": (PreparedDocument, "prepared-document"),
                   "lab": (PreparedLabRecord, "prepared-lab-record")}[profile]
    schema = model.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"urn:amphora:evidence.{name}:1:validation"
    raw = (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
           + "\n").encode("utf-8")
    return SchemaRef(schema_id="evidence." + name, version="1", sha256=hashlib.sha256(raw).hexdigest())
