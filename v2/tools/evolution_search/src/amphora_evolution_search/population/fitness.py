"""Intrinsic fitness/evaluation linkage; assembly and evidence authority stay external."""

from dataclasses import dataclass

from amphora_contracts_population import FitnessRecord

from ..ranking import CandidateScore, require
from .evaluations import FrozenEvaluations
from .specification import canonical


@dataclass(frozen=True)
class FitnessEvidence:
    evaluations: FrozenEvaluations
    observations: tuple

    def __post_init__(self):
        object.__setattr__(self, "observations", self.evaluations.terminal(self.observations))

    def bind(self, record):
        return BoundFitness(self, record)


@dataclass(frozen=True)
class BoundFitness:
    evidence: FitnessEvidence
    record: FitnessRecord

    def __post_init__(self):
        checked = FitnessRecord.model_validate_json(self.record.model_dump_json())
        object.__setattr__(self, "record", checked)
        require(len(canonical(checked)) <= 8192, "fitness_bytes")
        frozen = self.evidence.evaluations
        original = frozen.membership.original.record
        require(checked.generation == frozen.membership.identity, "fitness_generation")
        require(checked.candidate_id in {member.candidate_id for member in frozen.membership.members}, "fitness_candidate")
        require(checked.assembly == original.assembly.tool and checked.policy == original.assembly.policy,
                "fitness_assembly_policy")
        require(checked.evaluation_set_sha256 == frozen.digest, "fitness_evaluation_set")
        observations = {item.evaluation_sha256: item for item in self.evidence.observations
                        if item.key.candidate_id == checked.candidate_id}
        required = {method.method_id for method in original.method_graph.methods if method.required}
        unavailable = [item for item in observations.values() if item.key.method_id in required
                       and item.outcome.status != "evaluated"]
        if checked.outcome.status == "unavailable":
            return  # Retain an explicit assembly/unavailable failure, never create a score.
        require(not unavailable, "fitness_required_unavailable")
        actual = checked.outcome.objectives
        expected = original.assembly.objectives
        require(len(actual) == len(expected), "fitness_objective_count")
        for result, binding in zip(actual, expected, strict=True):
            require((result.value.objective_id, result.value.unit) == (binding.objective.objective_id, binding.objective.unit),
                    "fitness_objective_identity")
            require(len(set(result.evaluations)) == len(result.evaluations), "fitness_evidence_duplicate")
            require(all(key in observations and observations[key].outcome.status == "evaluated" for key in result.evaluations),
                    "fitness_evidence_unavailable")
            require({observations[key].key.method_id for key in result.evaluations} == set(binding.method_ids),
                    "fitness_objective_methods")

    @property
    def score(self):
        require(self.record.outcome.status == "evaluated", "fitness_not_available")
        value = self.record.outcome
        return CandidateScore(self.record.candidate_id, tuple(o.value.value for o in value.objectives), value.constraint_violation)
