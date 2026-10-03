"""Exact report-to-experiment matching does not adjudicate quality or promote evidence."""
from dataclasses import dataclass

from ..experiments.model import Experiment
from .identity import require
from .records import Observation
from .series import SeriesValue
from .values import CategoryValue, CensoredValue, MissingValue, NumericValue


@dataclass(frozen=True, slots=True)
class ObservationMatch:
    reasons: tuple[str, ...]
    state_known: bool

    @property
    def disposition(self):
        return "quarantined" if self.reasons else "matched"

    @classmethod
    def reconcile(cls, observation, experiment):
        require(type(observation) is Observation and type(experiment) is Experiment,"matching_records_required")
        reasons = []
        binding = observation.binding
        if observation.identity.reference.scope != experiment.identity.reference.scope:
            reasons.append("observation_scope_mismatch")
        if binding.target.experiment != experiment.identity.reference:
            reasons.append("experiment_revision_mismatch")
        if binding.measurement.method != experiment.protocol.method:
            reasons.append("method_mismatch")
        if binding.measurement.context != experiment.protocol.applicability:
            reasons.append("context_mismatch")
        expected = experiment.expectation(binding.target.expectation_id)
        if expected is None:
            return cls(tuple(reasons+["unknown_expectation"]),False)
        sample = experiment.sample(expected.sample)
        if binding.specimen.sample != expected.sample:
            reasons.append("sample_revision_mismatch")
        if binding.specimen.material_state != sample.sample.record.material_state:
            reasons.append("material_state_revision_mismatch")
        if binding.target.replicate_id != expected.replicate.replicate_id:
            reasons.append("replicate_mismatch")
        if binding.role != expected.replicate.role:
            reasons.append("control_role_mismatch")
        value, spec = observation.value, expected.readout
        allowed = {"numeric":(NumericValue,CensoredValue,MissingValue),"categorical":(CategoryValue,MissingValue),
                   "series":(SeriesValue,MissingValue)}[spec.kind]
        if type(value) not in allowed:
            reasons.append("readout_kind_mismatch")
        elif type(value) is SeriesValue:
            if (value.x_unit,value.y_unit) != (spec.x_unit,spec.unit):
                reasons.append("readout_unit_mismatch")
        elif type(value) in (NumericValue,CensoredValue) and value.unit != spec.unit:
            reasons.append("readout_unit_mismatch")
        return cls(tuple(reasons),sample.state is not None)
