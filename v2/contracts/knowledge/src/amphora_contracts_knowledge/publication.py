"""Owned reasoning publication requests/status; no caller-supplied authority."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_artifacts import DerivationReceipt
from amphora_contracts_core import Identifier, SchemaRef, WireModel
from amphora_contracts_graph_runtime import DomainReceipt
from pydantic import Field

from .reasoning import ReasoningResult
from .references import DomainGraphRef


class ReasoningPublicationRequest(WireModel):
    wire_version: Literal["1"]
    graph: DomainGraphRef
    publication_id: Identifier
    reasoning_request_id: Identifier


class ReasoningPublicationPending(WireModel):
    status: Literal["pending"] = "pending"


class ReasoningPublicationFailed(WireModel):
    status: Literal["failed"] = "failed"
    code: Identifier
    external_effects: Literal["none", "possible"]


class ReasoningPublicationPublished(WireModel):
    status: Literal["published"] = "published"
    derivation: DerivationReceipt
    receipt: DomainReceipt


class ReasoningPublicationStatus(WireModel):
    wire_version: Literal["1"]
    request: ReasoningPublicationRequest
    actor_id: Identifier
    outcome: Annotated[ReasoningPublicationPending | ReasoningPublicationFailed | ReasoningPublicationPublished,
                       Field(discriminator="status")]


def reasoning_artifact_schema_document() -> bytes:
    """Self-contained Data payload profile; not the exporter schema's URN/base."""
    document = ReasoningResult.model_json_schema(mode="validation")
    document["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return (json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()


def reasoning_artifact_schema() -> SchemaRef:
    return SchemaRef(schema_id="knowledge.reasoning-result.payload", version="1",
                     sha256=hashlib.sha256(reasoning_artifact_schema_document()).hexdigest())
