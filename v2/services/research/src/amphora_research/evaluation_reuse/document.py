from dataclasses import dataclass

from amphora_contracts_evaluation_reuse import ReuseCandidateEvidence, ReuseEvaluationEvidence, ReuseProjection, ReuseRef

from ..fitness.reuse import canonical, digest
from .errors import require


def bounded(value):
    content = canonical(value)
    require(len(content) <= 8388608, 'reuse_document_limit')
    return content


def candidate_evidence(candidate,key,canonicalization):
    return ReuseCandidateEvidence(candidate=candidate,declaration=key.record,
        producer=canonicalization.production.proof,canonicalization=canonicalization.receipt)


@dataclass(frozen=True, slots=True)
class ReuseDocument:
    record: ReuseProjection
    content: bytes

    @classmethod
    def prepare(cls, configured, request, actor, qualification, sources):
        configured.bind(request)
        q = qualification
        require(q.policy == configured.policy, 'reuse_qualification_policy_mismatch')
        record = ReuseProjection(wire_version='1',authority='synthetic_reuse_decision',
            reference=ReuseRef(scope=configured.record.scope,reuse_id=request.reuse_id,sha256='0'*64),
            actor_id=actor,profile=configured.record,request=request,
            source=candidate_evidence(q.subjects.source,q.source,q.source_canonicalization),
            target=candidate_evidence(q.subjects.target,q.target,q.target_canonicalization),
            evaluation=ReuseEvaluationEvidence(producer=q.evaluation.production.proof,receipt=q.evaluation.receipt),
            eligibility=q.subjects.eligibility,synthesis=q.subjects.synthesis,status=q.status,
            reusable_artifact=q.reusable_artifact,reasons=q.reasons,focus=q.subjects.focus,
            sources=tuple(sorted(sources,key=lambda source:source.artifact_id)))
        reference = record.reference.model_copy(update={'sha256':digest({'format':'research.evaluation-reuse.v1',
            'scope':record.reference.scope.model_dump(mode='json'),'reuse_id':record.reference.reuse_id,
            'projection':record.model_dump(mode='json',exclude={'reference'})})})
        record = record.model_copy(update={'reference':reference})
        return cls(record,bounded(record.model_dump(mode='json')))
