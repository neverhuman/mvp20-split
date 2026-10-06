"""Private versioned evaluation file DTOs; domain policy lives in protocol/scoring."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, WireModel
from amphora_contracts_planning import CallLimits, ModelBinding
from pydantic import Field

BasisPoints = Annotated[int, Field(ge=0, le=10000)]


class AssertionRecord(WireModel):
    assertion_id: Identifier
    pointer: Annotated[str, Field(max_length=1024)]
    operation: Literal['equals', 'contains']
    expected_json: Annotated[str, Field(min_length=1, max_length=8192)]


class CaseRecord(WireModel):
    case_id: Identifier
    category: Identifier
    input_sha256: Digest
    allow_abstention: bool
    hard_authority: bool
    assertions: Annotated[tuple[AssertionRecord, ...], Field(min_length=1, max_length=128)]


class CorpusRecord(WireModel):
    schema_version: Literal['1'] = '1'
    cases: Annotated[tuple[CaseRecord, ...], Field(min_length=1, max_length=256)]


class CategoryRecord(WireModel):
    category: Identifier
    minimum_score: BasisPoints
    maximum_abstention: BasisPoints


class ManifestRecord(WireModel):
    schema_version: Literal['1'] = '1'
    suite_id: Identifier
    mode: Literal['fixture', 'live']
    adapter_revision: Identifier
    model: ModelBinding
    prompt_sha256: Digest
    corpus_sha256: Digest
    allowed_data: Annotated[tuple[ArtifactRef, ...], Field(max_length=256)]
    limits: CallLimits
    repetitions: Annotated[int, Field(ge=1, le=16)]
    categories: Annotated[tuple[CategoryRecord, ...], Field(min_length=1, max_length=32)]


class ObservationRecord(WireModel):
    schema_version: Literal['1'] = '1'
    protocol_sha256: Digest
    case_id: Identifier
    repetition: Annotated[int, Field(ge=1, le=16)]
    status: Literal['proposed', 'scientific_abstention', 'provider_error', 'invalid', 'unknown', 'authority_violation']
    payload_json: Annotated[str, Field(max_length=65536)] | None
