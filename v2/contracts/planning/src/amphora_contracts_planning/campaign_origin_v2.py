"""Additive origin projection with explicit consumed Knowledge graph pins."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, SchemaRef, WireModel
from amphora_contracts_knowledge import (
    AssertionRevisionRef, DomainGraphRef, DomainHead, EntityRevisionRef, StructuralPolicyRef, VocabularyRef,
)
from pydantic import Field
from .campaign_origin import CampaignOriginBody


class CampaignOriginKnowledge(WireModel):
    status: Literal['available', 'unavailable']
    graph: DomainGraphRef
    head: DomainHead | None
    vocabulary: VocabularyRef | None
    policy: StructuralPolicyRef | None
    entities: Annotated[tuple[EntityRevisionRef, ...], Field(max_length=256)]
    assertions: Annotated[tuple[AssertionRevisionRef, ...], Field(max_length=256)]
    selection_sha256: Digest
    context_sha256: Digest | None
    unavailable: Identifier | None


class CampaignOriginBodyV2(CampaignOriginBody):
    schema_version: Literal['2'] = '2'
    knowledge: CampaignOriginKnowledge | None


class CampaignOriginV2(WireModel):
    schema_version: Literal['2'] = '2'
    origin_sha256: Digest
    origin: CampaignOriginBodyV2


def campaign_origin_v2_schema():
    schema = CampaignOriginV2.model_json_schema(mode='validation')
    schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    schema['$id'] = 'urn:amphora:planning.campaign-origin-knowledge:1:validation'
    raw = (json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode()
    return SchemaRef(schema_id='planning.campaign-origin-knowledge', version='1', sha256=hashlib.sha256(raw).hexdigest())
