"""Exact synthetic consensus preserves unavailable points and owner action gates."""
from dataclasses import dataclass

from amphora_contracts_evaluation_identity import ObjectiveAxis

from ..observations.measurement_wire import from_wire
from ..observations.values import NumericValue
from .evidence import FitnessEvidence
from .policy import FitnessPolicy, require
from .reuse import EvaluationKey, canonical


@dataclass(frozen=True, slots=True)
class FitnessAxis:
    specification: ObjectiveAxis
    reviews: tuple
    values: tuple
    reasons: tuple[str, ...]

    @property
    def amount(self):
        return None if self.reasons else self.values[0].quantity.value.amount

    @classmethod
    def assemble(cls, axis, evidence, state):
        expectations = evidence.expectations(axis, state)
        reviews, values, reasons = [], [], []
        if not expectations:
            reasons.append("missing_expectation")
        for expected in expectations:
            if expected.readout.kind != "numeric" or expected.readout.unit != axis.unit:
                reasons.append("readout_incompatible")
            matching = tuple(row for row in evidence.interpretation.reviews
                             if row.observation.binding.target.expectation_id == expected.expectation_id)
            if not matching:
                reasons.append("missing_observation")
            for row in matching:
                reviews.append(row)
                binding = row.observation.binding
                if (binding.target.experiment != evidence.interpretation.experiment.reference
                    or binding.specimen.sample != expected.sample or binding.specimen.material_state != state
                    or binding.role != "sample" or binding.target.replicate_id != expected.replicate.replicate_id):
                    reasons.append("observation_binding_mismatch")
                if row.disposition != "usable" or row.effective_match.disposition != "matched":
                    reasons.append("observation_unusable")
                measurement = row.observation.value
                if row.normalization is not None:
                    if row.normalization.status != "normalized" or row.normalization.normalized is None:
                        reasons.append("normalization_unresolved")
                    else:
                        measurement = row.normalization.normalized
                value = from_wire(measurement)
                values.append(value)
                if type(value) is not NumericValue:
                    reasons.append("measurement_" + value.kind)
                elif value.unit != axis.unit:
                    reasons.append("measurement_unit_mismatch")
        numeric = [value.quantity.value.amount for value in values if type(value) is NumericValue]
        if len(set(numeric)) > 1:
            reasons.append("conflicting_numeric_values")
        return cls(axis, tuple(reviews), tuple(values), tuple(dict.fromkeys(reasons)))


@dataclass(frozen=True, slots=True)
class FitnessAssembly:
    policy: FitnessPolicy
    key: EvaluationKey
    evidence: FitnessEvidence
    axes: tuple[FitnessAxis, ...]

    @classmethod
    def prepare(cls, policy, key, evidence):
        evidence.bind(policy, key)
        axes = tuple(FitnessAxis.assemble(axis, evidence, key.record.context.material_state) for axis in policy.evaluation.objectives)
        return cls(policy, key, evidence, axes)

    @property
    def synthesis_status(self):
        statuses = {item.disposition for item in self.evidence.synthesis.assessment.alternatives}
        return "eligible" if "eligible" in statuses else "blocked" if statuses == {"blocked"} else "unknown"

    @property
    def disposition(self):
        eligibility = self.evidence.eligibility.assessment.disposition
        if eligibility == "ineligible" or (self.policy.synthesis_required and self.synthesis_status == "blocked"):
            return "excluded"
        if (eligibility != "eligible" or any(axis.reasons for axis in self.axes)
            or (self.policy.synthesis_required and self.synthesis_status != "eligible")):
            return "unavailable"
        return "ready"

    @property
    def focus(self):
        result = list(self.evidence.eligibility.assessment.focus)
        if self.synthesis_status != "eligible":
            result.append("synthesis_" + self.synthesis_status)
        for axis in self.axes:
            result.extend(axis.reasons)
            for review in axis.reviews:
                result.extend(review.focus)
        return tuple(dict.fromkeys(result))

    @property
    def comparison_context(self):
        inputs = sorted((item.model_dump(mode="json") for item in self.key.record.context.inputs), key=lambda item:item["name"])
        return canonical({"policy":self.policy.reference.model_dump(mode="json"),
                          "scope":self.key.record.context.scope.model_dump(mode="json"), "inputs":inputs})

    def dominates(self, other):
        require(self.comparison_context == other.comparison_context, "fitness_comparison_context_mismatch")
        require(self.disposition == other.disposition == "ready", "fitness_comparison_requires_ready")
        comparisons = [(first.amount <= second.amount, first.amount < second.amount)
                       if first.specification.direction == "minimize" else
                       (first.amount >= second.amount, first.amount > second.amount)
                       for first, second in zip(self.axes, other.axes, strict=True)]
        return all(item[0] for item in comparisons) and any(item[1] for item in comparisons)
