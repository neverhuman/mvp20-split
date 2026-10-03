"""Exact subject/context and attributed adapter claims for a bounded purpose."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, Identifier, SchemaRef
from amphora_contracts_research import CandidateRevisionRef, MaterialStateRevisionRef, SampleRevisionRef
from pydantic import TypeAdapter, ValidationError

from ..observations.identity import ObservationReference

IDENTIFIER = TypeAdapter(Identifier)
KINDS = ("measurement","model","synthesis")


class EligibilityError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise EligibilityError(reason)


def identifier(value):
    try:
        IDENTIFIER.validate_python(value,strict=True)
    except ValidationError as error:
        raise EligibilityError("invalid_eligibility_identifier") from error


def names(items):
    require(type(items) is tuple and len(items) <= 64,"eligibility_flag_bound")
    for item in items:
        identifier(item)
    require(len(set(items)) == len(items),"duplicate_eligibility_flag")


@dataclass(frozen=True, slots=True)
class DecisionSubject:
    candidate: CandidateRevisionRef
    material_state: MaterialStateRevisionRef | None
    sample: SampleRevisionRef | None

    def __post_init__(self):
        require(type(self.candidate) is CandidateRevisionRef,"eligibility_candidate_required")
        require(self.material_state is None or type(self.material_state) is MaterialStateRevisionRef,"eligibility_state_type")
        require(self.sample is None or type(self.sample) is SampleRevisionRef,"eligibility_sample_type")
        require(all(ref.scope == self.candidate.scope for ref in (self.material_state,self.sample) if ref is not None),
                "eligibility_subject_scope_mismatch")


@dataclass(frozen=True, slots=True)
class DecisionContext:
    subject: DecisionSubject
    domain: str
    purpose: str
    conditions: ArtifactRef

    def __post_init__(self):
        require(type(self.subject) is DecisionSubject,"decision_subject_required")
        identifier(self.domain)
        identifier(self.purpose)
        require(type(self.conditions) is ArtifactRef,"decision_context_required")
        require(self.conditions.scope == self.subject.candidate.scope,"decision_context_scope_mismatch")


@dataclass(frozen=True, slots=True)
class EvidenceOrigin:
    source: ArtifactRef
    method: SchemaRef
    kind: str
    authority: str
    observation: ObservationReference | None = None

    def __post_init__(self):
        require(type(self.source) is ArtifactRef,"eligibility_source_required")
        require(type(self.method) is SchemaRef,"eligibility_method_required")
        require(self.kind in KINDS,"invalid_eligibility_kind")
        require(self.authority in ("synthetic","scientific"),"invalid_evidence_authority")
        require(self.observation is None or type(self.observation) is ObservationReference,"eligibility_observation_type")
        if self.observation is not None:
            require(self.kind == "measurement" and self.observation.scope == self.source.scope,"eligibility_observation_mismatch")


@dataclass(frozen=True, slots=True)
class CriterionClaim:
    criterion_id: str
    context: DecisionContext
    origin: EvidenceOrigin
    disposition: str
    flags: tuple[str, ...]

    def __post_init__(self):
        identifier(self.criterion_id)
        require(type(self.context) is DecisionContext,"decision_context_required")
        require(type(self.origin) is EvidenceOrigin,"evidence_origin_required")
        require(self.origin.source.scope == self.context.subject.candidate.scope,"eligibility_source_scope_mismatch")
        require(self.disposition in ("supported","contradicted","unknown"),"invalid_criterion_disposition")
        names(self.flags)
