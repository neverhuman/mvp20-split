"""Reviewed synthetic input profiles and reference-only decision requests."""
import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, Scope, WireModel
from pydantic import Field

from .eligibility import EligibilityContext, EligibilityProfile
from .observations import ObservationRevisionRef
from .synthesis import RouteOptionRecord, SynthesisProfile


class ScientificInputProfileRef(WireModel):
    scope: Scope
    kind: Literal["eligibility","synthesis"]
    profile_id: Identifier
    version: Identifier
    sha256: Digest


class EligibilityInputProfile(WireModel):
    wire_version: Literal["1"]
    kind: Literal["eligibility"]
    profile_id: Identifier
    version: Identifier
    policy: EligibilityProfile
    adapter: SchemaRef
    publishers: Annotated[tuple[Identifier, ...],Field(min_length=1,max_length=32)]


class SynthesisInputProfile(WireModel):
    wire_version: Literal["1"]
    kind: Literal["synthesis"]
    profile_id: Identifier
    version: Identifier
    policy: SynthesisProfile
    adapter: SchemaRef
    publishers: Annotated[tuple[Identifier, ...],Field(min_length=1,max_length=32)]


class ScientificAssessmentRequest(WireModel):
    wire_version: Literal["1"]
    decision_id: Identifier
    profile: ScientificInputProfileRef
    reports: Annotated[tuple[ArtifactRef, ...],Field(min_length=1,max_length=16)]


class ReportedEligibilityOrigin(WireModel):
    source: ArtifactRef | None
    method: SchemaRef
    kind: Literal["measurement","model","synthesis"]
    authority: Literal["synthetic"]
    observation: ObservationRevisionRef | None


class ReportedEligibilityClaim(WireModel):
    criterion_id: Identifier
    context: EligibilityContext
    origin: ReportedEligibilityOrigin
    disposition: Literal["supported","contradicted","unknown"]
    flags: Annotated[tuple[Identifier, ...],Field(max_length=64)]


class SyntheticEligibilityReport(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    issuer: Identifier
    adapter: SchemaRef
    raw_report: ArtifactRef
    claims: Annotated[tuple[ReportedEligibilityClaim, ...],Field(max_length=1024)]


class SyntheticSynthesisReport(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    issuer: Identifier
    adapter: SchemaRef
    raw_report: ArtifactRef
    options: Annotated[tuple[RouteOptionRecord, ...],Field(min_length=1,max_length=64)]


def synthetic_scientific_report_schema_document(kind):
    models = {"eligibility":SyntheticEligibilityReport,"synthesis":SyntheticSynthesisReport}
    if kind not in models:
        raise ValueError("unknown_synthetic_scientific_report_kind")
    schema = models[kind].model_json_schema(mode="serialization")
    return json.dumps(schema,sort_keys=True,separators=(",", ":"),ensure_ascii=False,allow_nan=False).encode("utf-8")


def synthetic_scientific_report_schema(kind):
    return SchemaRef(schema_id="research.synthetic-"+kind+"-report.payload",version="1",
        sha256=hashlib.sha256(synthetic_scientific_report_schema_document(kind)).hexdigest())
