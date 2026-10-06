"""Explicit synthetic consensus policy, including uncertainty and synthesis posture."""
from dataclasses import dataclass

from amphora_contracts_core import SchemaRef
from amphora_contracts_evaluation_identity import EvaluationReusePolicy

from .reuse import canonical, digest


class FitnessError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise FitnessError(reason)


UNCERTAINTY = SchemaRef(schema_id="research.fitness-central-value", version="1",
    sha256=digest({"format":"research.fitness-central-value.v1", "uncertainty":"retain",
                   "ranking":"exact-central-value", "replicates":"exact-consensus"}))


@dataclass(frozen=True, slots=True)
class FitnessPolicy:
    evaluation: EvaluationReusePolicy
    observation_use: SchemaRef
    synthesis_required: bool

    def __post_init__(self):
        evaluation = EvaluationReusePolicy.model_validate_json(self.evaluation.model_dump_json())
        observation_use = SchemaRef.model_validate_json(self.observation_use.model_dump_json())
        object.__setattr__(self, "evaluation", evaluation)
        object.__setattr__(self, "observation_use", observation_use)
        require(type(self.synthesis_required) is bool, "fitness_explicit_synthesis_requirement")
        require(all(axis.uncertainty_policy == UNCERTAINTY for axis in evaluation.objectives), "fitness_uncertainty_policy")
        require({"conditions", "experiment-applicability"} <= set(evaluation.required_context), "fitness_context_requirements")
        require(evaluation.reference == self.reference, "fitness_policy_reference_mismatch")

    @staticmethod
    def descriptor(evaluation, observation_use, synthesis_required):
        result = evaluation.model_dump(mode="json", exclude={"reference"})
        result["required_context"].sort()
        return {"format":"research.fitness-consensus.v1", "evaluation":result,
                "observation_use":observation_use.model_dump(mode="json"), "synthesis_required":synthesis_required}

    @property
    def reference(self):
        return SchemaRef(schema_id="research.fitness-consensus", version="1",
            sha256=digest(self.descriptor(self.evaluation, self.observation_use, self.synthesis_required)))

    @classmethod
    def prepare(cls, evaluation, observation_use, synthesis_required):
        reference = SchemaRef(schema_id="research.fitness-consensus", version="1",
            sha256=digest(cls.descriptor(evaluation, observation_use, synthesis_required)))
        return cls(evaluation.model_copy(update={"reference":reference}), observation_use, synthesis_required)

    @property
    def bytes(self):
        return canonical(self.descriptor(self.evaluation, self.observation_use, self.synthesis_required))
