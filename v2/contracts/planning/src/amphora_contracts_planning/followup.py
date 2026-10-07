"""Explicit criterion targets for future campaigns; shape validation grants no authority."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SchemaRef, WireModel
from amphora_contracts_research import EvidenceNeedRef, ResearchQuestionRef
from pydantic import Field

from .campaign_context import CampaignAssessmentSelection, CampaignResearchSelection
from .campaign_output import CampaignDraft, Description, FutureCampaignDraft


class CampaignCriterionRef(WireModel):
    question: ResearchQuestionRef
    need: EvidenceNeedRef
    criterion_id: Identifier
    assessment: CampaignAssessmentSelection | None


class CampaignCriterionTarget(WireModel):
    criterion: CampaignCriterionRef
    improvement: Description
    expected_learning: Description


class CriterionUnresolvedPoint(WireModel):
    criterion: CampaignCriterionRef
    posture: Literal['unknown', 'weak', 'contradictory', 'missing', 'inapplicable']
    description: Description


class CampaignFollowupSelection(CampaignResearchSelection):
    schema_version: Literal['2'] = '2'
    criteria: Annotated[tuple[CampaignCriterionRef, ...], Field(max_length=64)]
    focus_artifact: ArtifactRef | None


class CheckpointFollowupDraft(CampaignDraft):
    schema_version: Literal['3'] = '3'
    candidate: FutureCampaignDraft | None
    targets: Annotated[tuple[CampaignCriterionTarget, ...], Field(max_length=32)]
    unresolved: Annotated[tuple[CriterionUnresolvedPoint, ...], Field(max_length=64)]
    focus_artifact: ArtifactRef | None


def _profile(record, name):
    schema = record.model_json_schema(mode='validation')
    schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    schema['$id'] = f'urn:amphora:{name}:1:validation'
    raw = (json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
    return SchemaRef(schema_id=name, version='1', sha256=hashlib.sha256(raw).hexdigest())


def campaign_followup_selection_schema() -> SchemaRef:
    return _profile(CampaignFollowupSelection, 'planning.campaign-followup-selection')


def checkpoint_followup_draft_schema() -> SchemaRef:
    return _profile(CheckpointFollowupDraft, 'planning.checkpoint-followup-draft')
