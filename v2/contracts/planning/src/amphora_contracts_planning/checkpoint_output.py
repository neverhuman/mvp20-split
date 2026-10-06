"""Explicit concrete materialization proposals; predecessor campaign output stays closed."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_campaigns import ActivationPath
from amphora_contracts_core import Digest, Identifier, SchemaRef, WireModel
from amphora_contracts_graph_runtime import GraphReadCut, ScalarValue
from pydantic import Field

from .campaign_output import CampaignDraft, CampaignEvidenceIntent, FutureCampaignDraft


class MaterializationFieldProposal(WireModel):
    target: ActivationPath
    field_name: Identifier
    previous_value_sha256: Digest
    proposed: ScalarValue


class MaterializationAdjustmentDraft(WireModel):
    kind: Literal['materialization_adjustment']
    cut: GraphReadCut
    checkpoint_seed_sha256: Digest
    changes: Annotated[tuple[MaterializationFieldProposal, ...], Field(min_length=1, max_length=64)]
    expected_evidence: Annotated[tuple[CampaignEvidenceIntent, ...], Field(max_length=64)]


class CheckpointDraft(CampaignDraft):
    schema_version: Literal['2'] = '2'
    candidate: Annotated[FutureCampaignDraft | MaterializationAdjustmentDraft, Field(discriminator='kind')] | None


def checkpoint_draft_schema() -> SchemaRef:
    schema = CheckpointDraft.model_json_schema(mode='validation')
    schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    schema['$id'] = 'urn:amphora:planning.checkpoint-draft:1:validation'
    raw = (json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
    return SchemaRef(schema_id='planning.checkpoint-draft', version='1', sha256=hashlib.sha256(raw).hexdigest())
