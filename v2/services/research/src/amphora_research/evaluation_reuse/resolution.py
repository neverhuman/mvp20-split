"""Public producer/Data reads and exact owner history resolution precede SQL publication."""
from amphora_contracts_core import ArtifactRef
from amphora_contracts_evaluation_identity import EvaluationIdentityInput
from pydantic import BaseModel

from ..candidate_registration.registration import CandidateReader
from ..fitness.reuse import EvaluationKey
from ..scientific_api.records import ScientificRecords
from .errors import require
from .evidence import CanonicalEvidence, EvaluationEvidence, read_document
from .policy import ReuseQualification, ReuseSubjects
from .producer import ProducerSelection


def dependencies(*values):
    found = {}
    def visit(value):
        if isinstance(value, ArtifactRef):
            previous = found.setdefault(value.artifact_id,value)
            require(previous == value, 'reuse_artifact_identity_conflict')
            require(len(found) <= 128, 'reuse_source_limit')
        elif isinstance(value, BaseModel):
            for name in type(value).model_fields:
                visit(getattr(value,name))
        elif isinstance(value, tuple):
            for item in value:
                visit(item)
    for value in values:
        visit(value)
    return tuple(found[name] for name in sorted(found))


class ReuseResolver:
    def __init__(self, ledger):
        self.candidates = CandidateReader(ledger)
        self.science = ScientificRecords(ledger.engine)

    def resolve(self, principal, configured, request, data, runtime):
        configured.bind(request)
        principal.require('read_candidate',configured.record.scope)
        principal.require('read_scientific_record',configured.record.scope)
        source = self.candidates.read(principal,request.source.candidate)
        target = self.candidates.read(principal,request.target.candidate)
        eligibility = self.science.decision(principal,request.eligibility)
        synthesis = self.science.decision(principal,request.synthesis)
        require(all(value is not None for value in (source,target,eligibility,synthesis)), 'reuse_owner_record_unavailable')
        subjects = ReuseSubjects(source,target,eligibility,synthesis)
        keys, canonicalizations = [], []
        for selected in (request.source,request.target):
            declaration = read_document(data,selected.identity,EvaluationIdentityInput,'evaluation-identity.input')
            key = EvaluationKey(declaration)
            selection = selected.canonicalization
            proof = runtime.read(ProducerSelection(selection.scope,selection.run_id,selection.completion_id))
            canonicalizations.append(CanonicalEvidence.resolve(proof,configured.record.canonicalizer,declaration,data))
            keys.append(key)
        selected = request.evaluation
        proof = runtime.read(ProducerSelection(selected.scope,selected.run_id,selected.completion_id))
        evaluation = EvaluationEvidence.resolve(proof,configured.record.evaluation,request.source.identity,data)
        qualification = ReuseQualification.prepare(configured.policy,*keys,subjects,*canonicalizations,evaluation)
        sources = dependencies(request,source,target,eligibility,synthesis,*(key.record for key in keys),
            *(item.production.proof for item in canonicalizations),evaluation.production.proof)
        require(all(item.scope == principal.scope for item in sources), 'reuse_source_scope_mismatch')
        for reference in sources:
            data.read(reference)
        return qualification, sources
