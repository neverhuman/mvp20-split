"""Private composition of owner records; resolution/authentication belongs to the service boundary."""
from dataclasses import dataclass, fields

from amphora_contracts_research import CandidateRevision, EligibilityDecision, ObservationUseProjection, SynthesisDecision

from .policy import require


@dataclass(frozen=True, slots=True)
class FitnessEvidence:
    candidate: CandidateRevision
    interpretation: ObservationUseProjection
    eligibility: EligibilityDecision
    synthesis: SynthesisDecision

    def __post_init__(self):
        for field in fields(self):
            record = getattr(self, field.name)
            object.__setattr__(self, field.name, field.type.model_validate_json(record.model_dump_json()))

    def bind(self, policy, key):
        candidate, use = self.candidate, self.interpretation
        eligibility, synthesis = self.eligibility.assessment, self.synthesis.assessment
        context, evaluation = key.record.context, key.record.policy
        require(evaluation == policy.evaluation, "fitness_evaluation_policy_mismatch")
        require(all(record.reference.scope == context.scope for record in
                    (candidate, use, self.eligibility, self.synthesis)), "fitness_scope_mismatch")
        require(candidate.representation == key.record.representation.source, "fitness_candidate_representation_mismatch")
        require(use.profile.scope == context.scope and use.experiment.reference.scope == context.scope,
                "fitness_interpretation_scope_mismatch")
        require(use.profile.policy.reference == policy.observation_use and use.profile.policy.action == evaluation.purpose,
                "fitness_interpretation_policy_mismatch")
        require(use.experiment.protocol.method == evaluation.method.method, "fitness_method_mismatch")
        require(eligibility.policy.reference == evaluation.method.applicability, "fitness_eligibility_policy_mismatch")
        require(synthesis.policy.reference == evaluation.synthesis_policy, "fitness_synthesis_policy_mismatch")
        subject = eligibility.policy.context.subject
        require(subject.candidate == candidate.reference and subject.material_state == context.material_state,
                "fitness_eligibility_subject_mismatch")
        require(synthesis.policy.context.candidate == candidate.reference, "fitness_synthesis_subject_mismatch")
        require(eligibility.policy.context.purpose == synthesis.policy.context.purpose == evaluation.purpose,
                "fitness_purpose_mismatch")
        require(eligibility.policy.context.domain == synthesis.policy.context.domain, "fitness_domain_mismatch")
        contexts = {item.name:item.artifact for item in context.inputs}
        require(contexts["conditions"] == eligibility.policy.context.conditions == synthesis.policy.context.conditions,
                "fitness_conditions_mismatch")
        require(contexts["experiment-applicability"] == use.experiment.protocol.applicability,
                "fitness_experiment_applicability_mismatch")
        require(self.eligibility.reference.kind == "eligibility" and self.synthesis.reference.kind == "synthesis",
                "fitness_decision_kind_mismatch")
        require(len({row.observation.reference.observation_id for row in use.reviews}) == len(use.reviews),
                "fitness_duplicate_observation")
        require(all(row.observation.reference.scope == context.scope for row in use.reviews), "fitness_observation_scope_mismatch")
        require(len({item.expectation_id for item in use.experiment.expectations}) == len(use.experiment.expectations),
                "fitness_duplicate_expectation")
        require(len({item.sample.reference for item in use.experiment.samples}) == len(use.experiment.samples),
                "fitness_duplicate_sample")
        return self

    def expectations(self, axis, state):
        """Controls and other candidate/state specimens cannot supply this candidate's fitness."""
        subject_sample = self.eligibility.assessment.policy.context.subject.sample
        samples = {item.sample.reference for item in self.interpretation.experiment.samples
                   if item.sample.candidate == self.candidate.reference and item.sample.material_state == state
                   and (subject_sample is None or item.sample.reference == subject_sample)}
        return tuple(item for item in self.interpretation.experiment.expectations
                     if item.sample in samples and item.replicate.role == "sample" and item.readout.criterion_id == axis.objective_id)
