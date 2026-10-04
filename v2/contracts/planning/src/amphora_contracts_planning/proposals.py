"""Initial reference-only proposal profile; not a domain mutation command."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, WireModel
from pydantic import Field

from .context import ProposalAction
from .engagement import ProviderAttemptRef, ProviderUsage


class ReferenceProposal(WireModel):
    schema_version: Literal["1"] = "1"
    action: ProposalAction
    rationale: Annotated[str, Field(min_length=1, max_length=4096)]
    payload: ArtifactRef | None


class ProviderObservation(WireModel):
    schema_version: Literal["1"] = "1"
    attempt: ProviderAttemptRef
    status: Literal["proposed", "abstained", "invalid", "unavailable", "policy_rejected", "unknown"]
    reason_code: Identifier | None
    output_sha256: Digest
    captured_bytes: Annotated[int, Field(ge=0, le=65536)]
    output_complete: bool
    usage: ProviderUsage
    proposal: ReferenceProposal | None


def reference_proposal_schema() -> SchemaRef:
    schema = ReferenceProposal.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "urn:amphora:planning.reference-proposal:1:validation"
    raw = (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False) + "\n").encode("utf-8")
    return SchemaRef(schema_id="planning.reference-proposal", version="1",
                     sha256=hashlib.sha256(raw).hexdigest())
