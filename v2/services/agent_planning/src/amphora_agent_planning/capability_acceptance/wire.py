"""Versioned evidence document carried by the approved ArtifactRef inputs."""
import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_campaign_curation import CapabilityRequestRef
from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, WireModel
from amphora_contracts_tools import LockEntry
from pydantic import Field

Description = Annotated[str, Field(min_length=1, max_length=2048)]


class CriterionRecord(WireModel):
    index: Annotated[int, Field(ge=0, le=15)]
    criterion: Description
    result: Literal['passed', 'failed', 'unknown']
    method: Description
    observation: Description
    supporting_artifacts: Annotated[tuple[ArtifactRef, ...], Field(max_length=16)]


class AcceptanceRecord(WireModel):
    profile: Literal['planning.capability-acceptance.v1']
    authority: Literal['owner_reviewed_fulfillment_evidence']
    scientific_authority: Literal['not_established']
    request: CapabilityRequestRef
    proposal_sha256: Digest
    gap_key: Identifier
    release: LockEntry
    requested_applicability: Annotated[tuple[Description, ...], Field(min_length=1, max_length=16)]
    descriptor_applicability: Annotated[tuple[Description, ...], Field(min_length=1, max_length=64)]
    applicability_rationale: Description
    criteria: Annotated[tuple[CriterionRecord, ...], Field(min_length=1, max_length=16)]


def schema_bytes():
    value = AcceptanceRecord.model_json_schema(mode='validation')
    value['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    value['$id'] = 'urn:amphora:planning.capability-acceptance:1:validation'
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def acceptance_schema():
    return SchemaRef(schema_id='planning.capability-acceptance', version='1', sha256=hashlib.sha256(schema_bytes()).hexdigest())
