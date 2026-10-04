"""Explicit attributed edit candidates; accepted revisions remain Knowledge-owned."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SchemaRef, WireModel
from amphora_contracts_knowledge import AssertionRevisionRef, EntityRevisionRef
from pydantic import Field

from .extraction import ExtractionAttribution, ExtractionDraft, ExtractionEntity, ExtractionTask


class ExtractionTaskV2(ExtractionTask):
    schema_version: Literal["2"] = "2"
    existing_assertions: Annotated[tuple[AssertionRevisionRef, ...], Field(max_length=128)]


class ExtractionEntityV2(ExtractionEntity):
    context: ArtifactRef | None


class EditCandidate(WireModel):
    local_id: Identifier
    attribution: ExtractionAttribution


class AssertionCorrectionDraft(EditCandidate):
    operation: Literal["correct_assertion"]
    prior: AssertionRevisionRef
    replacement_local_id: Identifier


class AssertionRetractionDraft(EditCandidate):
    operation: Literal["retract_assertion"]
    assertion: AssertionRevisionRef


class EntityMergeDraft(EditCandidate):
    operation: Literal["merge_entities"]
    source: EntityRevisionRef
    target: EntityRevisionRef


class EntityContextRevisionDraft(EditCandidate):
    operation: Literal["revise_entity_context"]
    prior: EntityRevisionRef
    replacement_local_id: Identifier


ExtractionEdit = Annotated[
    AssertionCorrectionDraft | AssertionRetractionDraft | EntityMergeDraft | EntityContextRevisionDraft,
    Field(discriminator="operation"),
]


class ExtractionDraftV2(ExtractionDraft):
    schema_version: Literal["2"] = "2"
    entities: Annotated[tuple[ExtractionEntityV2, ...], Field(max_length=64)]
    edits: Annotated[tuple[ExtractionEdit, ...], Field(max_length=64)]


def extraction_edit_schema() -> SchemaRef:
    schema = ExtractionDraftV2.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "urn:amphora:planning.extraction-edit-draft:1:validation"
    raw = (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False) + "\n").encode("utf-8")
    return SchemaRef(schema_id="planning.extraction-edit-draft", version="1", sha256=hashlib.sha256(raw).hexdigest())
