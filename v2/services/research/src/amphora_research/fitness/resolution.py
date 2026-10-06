"""Resolve immutable Research records and current public Data reads before SQL writes."""
import hashlib
import json

from amphora_contracts_core import ArtifactRef, SchemaRef
from amphora_contracts_evaluation_identity import EvaluationIdentityInput
from pydantic import BaseModel

from ..assessment.reader import AssessmentPeerUnavailable, _decode
from ..candidate_registration.registration import CandidateReader
from ..observations.interpretation.store import InterpretationStore
from ..scientific_api.records import ScientificRecords
from .assembly import FitnessAssembly
from .evidence import FitnessEvidence
from .policy import FitnessError, require
from .reuse import EvaluationKey


def identity_schema():
    schema = EvaluationIdentityInput.model_json_schema(mode="validation")
    schema.update({"$schema":"https://json-schema.org/draft/2020-12/schema",
                   "$id":"urn:amphora:evaluation-identity.input:1:validation"})
    body = (json.dumps(schema,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
    return SchemaRef(schema_id="evaluation-identity.input",version="1",sha256=hashlib.sha256(body).hexdigest())


def artifact_dependencies(*values):
    found = {}
    def visit(value):
        if isinstance(value, ArtifactRef):
            old = found.setdefault(value.artifact_id, value)
            require(old == value, "fitness_artifact_identity_conflict")
            require(len(found) <= 128, "fitness_source_limit")
        elif isinstance(value, BaseModel):
            for name in type(value).model_fields:
                visit(getattr(value, name))
        elif isinstance(value, tuple):
            for item in value:
                visit(item)
    for value in values:
        visit(value)
    return tuple(found[name] for name in sorted(found))


class FitnessResolver:
    def __init__(self, ledger):
        self.candidates = CandidateReader(ledger)
        self.interpretations = InterpretationStore(ledger.engine)
        self.science = ScientificRecords(ledger.engine)

    def resolve(self, principal, configured, request, reader):
        configured.bind(request)
        principal.require("read_candidate", request.candidate.scope)
        principal.require("read_observation_interpretation", request.interpretation.scope)
        principal.require("read_scientific_record", request.eligibility.scope)
        candidate = self.candidates.read(principal, request.candidate)
        interpretation = self.interpretations.read(principal.scope, principal.actor_id, "observation-use", request.interpretation.interpretation_id)
        eligibility = self.science.decision(principal, request.eligibility)
        synthesis = self.science.decision(principal, request.synthesis)
        require(candidate is not None and interpretation is not None and interpretation.result is not None
                and eligibility is not None and synthesis is not None, "fitness_owner_record_unavailable")
        require(interpretation.result.reference == request.interpretation, "fitness_interpretation_reference_mismatch")
        evidence = FitnessEvidence(candidate, interpretation.result, eligibility, synthesis)
        source = request.declared_identity
        require(source.schema_ref == identity_schema() and source.media_type == "application/json"
                and source.size_bytes <= 262144, "fitness_identity_encoding_mismatch")
        raw = reader.read(source)
        require(len(raw) == source.size_bytes and hashlib.sha256(raw).hexdigest() == source.sha256, "fitness_identity_bytes_mismatch")
        try:
            declared = _decode(EvaluationIdentityInput, raw)
        except AssessmentPeerUnavailable as error:
            raise FitnessError("fitness_identity_document_invalid") from error
        key = EvaluationKey(declared)
        assembly = FitnessAssembly.prepare(configured.policy, key, evidence)
        sources = artifact_dependencies(source, key.record, evidence.candidate, evidence.interpretation, evidence.eligibility, evidence.synthesis)
        require(all(item.scope == principal.scope for item in sources), "fitness_source_scope_mismatch")
        for reference in sources:
            reader.read(reference)
        return assembly, sources
