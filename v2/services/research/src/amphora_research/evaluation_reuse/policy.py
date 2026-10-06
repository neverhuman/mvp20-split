"""Synthetic reuse qualification: candidate-context evidence, never measurement transfer."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, SchemaRef, Scope
from amphora_contracts_evaluation_identity import EvaluationReusePolicy
from amphora_contracts_research import CandidateRevision, EligibilityDecision, SynthesisDecision
from amphora_contracts_tools import ToolBinding

from ..fitness.reuse import EvaluationKey, digest
from .errors import require
from .evidence import CanonicalEvidence, EvaluationEvidence


@dataclass(frozen=True, slots=True)
class ReusePolicy:
    scope: Scope
    evaluation: EvaluationReusePolicy
    canonicalizer: ToolBinding
    synthesis_required: bool

    def __post_init__(self):
        for name, model in (('scope', Scope), ('evaluation', EvaluationReusePolicy), ('canonicalizer', ToolBinding)):
            value = getattr(self, name)
            object.__setattr__(self, name, model.model_validate_json(value.model_dump_json()))
        require(type(self.synthesis_required) is bool, 'reuse_synthesis_requirement_invalid')
        policy = self.evaluation
        require(policy.purpose == 'synthetic-cache-qualification'
            and policy.method.evaluator.capability_id == 'synthetic.digest-score'
            and self.canonicalizer.capability_id == 'synthetic.' + policy.representation.kind + '-canonicalize',
            'reuse_synthetic_capabilities_required')
        require(len(policy.objectives) == 1 and policy.objectives[0].objective_id == 'synthetic-digest-score'
            and policy.objectives[0].unit == '1' and policy.objectives[0].direction == 'minimize',
            'reuse_synthetic_objective_required')
        require('conditions' in policy.required_context, 'reuse_conditions_required')

    @property
    def reference(self):
        return SchemaRef(schema_id='research.synthetic-reuse', version='1', sha256=digest({
            'format':'research.synthetic-reuse.v1', 'scope':self.scope.model_dump(mode='json'),
            'evaluation':self.evaluation.model_dump(mode='json'),
            'canonicalizer':self.canonicalizer.model_dump(mode='json'),
            'synthesis_required':self.synthesis_required,
            'eligibility_scope':'candidate-state-without-sample',
            'synthesis_scope':'no-scale-or-purity-specialization'}))


@dataclass(frozen=True, slots=True)
class ReuseSubjects:
    source: CandidateRevision
    target: CandidateRevision
    eligibility: EligibilityDecision
    synthesis: SynthesisDecision

    def __post_init__(self):
        for name, model in (('source', CandidateRevision), ('target', CandidateRevision),
                            ('eligibility', EligibilityDecision), ('synthesis', SynthesisDecision)):
            object.__setattr__(self, name, model.model_validate_json(getattr(self, name).model_dump_json()))

    def bind(self, policy, source, target):
        require(all(record.reference.scope == policy.scope for record in
            (self.source, self.target, self.eligibility, self.synthesis)), 'reuse_owner_scope_mismatch')
        require(self.source.representation == source.record.representation.source
            and self.target.representation == target.record.representation.source, 'reuse_candidate_source_mismatch')
        require(self.eligibility.reference.kind == 'eligibility' and self.synthesis.reference.kind == 'synthesis',
            'reuse_decision_kind_mismatch')
        eligibility, synthesis = self.eligibility.assessment.policy, self.synthesis.assessment.policy
        require(eligibility.reference == policy.evaluation.method.applicability
            and synthesis.reference == policy.evaluation.synthesis_policy, 'reuse_owner_policy_mismatch')
        require(eligibility.context.subject.candidate == self.target.reference
            and eligibility.context.subject.material_state == target.record.context.material_state
            and synthesis.context.candidate == self.target.reference, 'reuse_target_subject_mismatch')
        require(eligibility.context.purpose == synthesis.context.purpose == policy.evaluation.purpose
            and eligibility.context.domain == synthesis.context.domain, 'reuse_owner_purpose_mismatch')
        conditions = {item.name:item.artifact for item in target.record.context.inputs}['conditions']
        require(eligibility.context.conditions == synthesis.context.conditions == conditions, 'reuse_conditions_mismatch')
        # The first synthetic oracle is candidate/state-wide, not specimen-, scale-
        # or purity-specific. Such qualified scientific reuse needs a later profile.
        require(eligibility.context.subject.sample is None
            and synthesis.context.scale is None and synthesis.context.purity is None,
            'reuse_specialized_context_unsupported')

    @property
    def synthesis_status(self):
        statuses = {item.disposition for item in self.synthesis.assessment.alternatives}
        return 'eligible' if 'eligible' in statuses else 'blocked' if statuses == {'blocked'} else 'unknown'

    @property
    def focus(self):
        points = ['eligibility.' + item for item in self.eligibility.assessment.focus]
        if self.synthesis_status != 'eligible':
            points.append('synthesis.' + self.synthesis_status)
        return tuple(sorted(set(points)))


@dataclass(frozen=True, slots=True)
class ReuseQualification:
    policy: ReusePolicy
    source: EvaluationKey
    target: EvaluationKey
    subjects: ReuseSubjects
    source_canonicalization: CanonicalEvidence
    target_canonicalization: CanonicalEvidence
    evaluation: EvaluationEvidence
    status: str
    reasons: tuple[str, ...]

    @property
    def reusable_artifact(self) -> ArtifactRef | None:
        return self.evaluation.production.output if self.status == 'permitted' else None

    @classmethod
    def prepare(cls, policy, source, target, subjects, source_canonicalization, target_canonicalization, evaluation):
        require(source.record.policy == target.record.policy == policy.evaluation, 'reuse_configured_policy_mismatch')
        require(source.record.context.scope == target.record.context.scope == policy.scope, 'reuse_context_scope_mismatch')
        subjects.bind(policy, source, target)
        for evidence, key in ((source_canonicalization, source), (target_canonicalization, target)):
            claim = key.record.representation
            receipt = evidence.receipt
            require(evidence.production.proof.invocation.tool == policy.canonicalizer
                and evidence.production.source == claim.source and receipt.canonical_sha256 == claim.canonical_sha256
                and receipt.source_sha256 == claim.source.sha256 and receipt.scope == policy.scope
                and receipt.kind == policy.evaluation.representation.kind
                and receipt.semantic_profile == claim.policy.semantic_profile
                and receipt.equivalence_profile == claim.policy.equivalence_profile, 'reuse_canonical_evidence_mismatch')
        require(evaluation.declaration == source.record
            and evaluation.production.proof.invocation.tool == policy.evaluation.method.evaluator
            and evaluation.receipt.method == policy.evaluation.method
            and evaluation.receipt.canonical_sha256 == source.record.representation.canonical_sha256
            and evaluation.receipt.value == int(source.record.representation.canonical_sha256[:6], 16),
            'reuse_evaluation_evidence_mismatch')
        reasons = []
        if not source.same_declared_identity(target):
            reasons.append('evaluation_context_mismatch')
        if subjects.eligibility.assessment.disposition != 'eligible':
            reasons.append('target_eligibility_' + subjects.eligibility.assessment.disposition)
        if policy.synthesis_required and subjects.synthesis_status != 'eligible':
            reasons.append('required_synthesis_' + subjects.synthesis_status)
        status = 'permitted' if not reasons else 'miss' if reasons == ['evaluation_context_mismatch'] else 'ineligible'
        return cls(policy, source, target, subjects, source_canonicalization, target_canonicalization,
                   evaluation, status, tuple(reasons))
