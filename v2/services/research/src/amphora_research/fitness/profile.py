"""Scoped reviewed configuration; wire validity alone does not select a policy."""
from dataclasses import dataclass

from amphora_contracts_fitness import FitnessProfile, FitnessProfileRef

from .policy import FitnessPolicy, require


@dataclass(frozen=True, slots=True)
class ConfiguredFitness:
    record: FitnessProfile

    def __post_init__(self):
        object.__setattr__(self, "record", FitnessProfile.model_validate_json(self.record.model_dump_json()))
        self.policy  # Verify content-derived policy reference at configuration time.

    @property
    def policy(self):
        return FitnessPolicy(self.record.evaluation, self.record.observation_use, self.record.synthesis_required)

    @property
    def reference(self):
        return FitnessProfileRef(scope=self.record.scope, policy=self.policy.reference)

    def bind(self, request):
        require(request.profile == self.reference, "fitness_profile_mismatch")
        require(all(reference.scope == self.record.scope for reference in
            (request.candidate, request.interpretation, request.eligibility, request.synthesis, request.declared_identity)),
            "fitness_request_scope_mismatch")
        require(request.interpretation.kind == "observation-use" and request.eligibility.kind == "eligibility"
                and request.synthesis.kind == "synthesis", "fitness_request_kind_mismatch")
        return request
