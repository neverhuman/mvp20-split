"""Synthetic producer payload; authenticity comes from Data's publication origin, not this JSON."""

import hashlib
import json
from typing import Literal

from amphora_contracts_core import ArtifactRef, Identifier, SchemaRef, WireModel

from .assessment import EvidenceCategory, EvidenceDisposition
from .questions import EvidenceNeedRef


class SyntheticEvidenceRecord(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    need: EvidenceNeedRef
    criterion_id: Identifier
    subject: ArtifactRef
    method: SchemaRef
    context: ArtifactRef
    category: EvidenceCategory
    issuer: Identifier
    purpose: Identifier
    disposition: EvidenceDisposition


def synthetic_evidence_schema_document() -> bytes:
    document = SyntheticEvidenceRecord.model_json_schema(mode="validation")
    document["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return (json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def synthetic_evidence_schema() -> SchemaRef:
    return SchemaRef(schema_id="research.synthetic-evidence.payload", version="1",
                     sha256=hashlib.sha256(synthetic_evidence_schema_document()).hexdigest())
