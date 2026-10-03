"""Output-only mappings preserve originals and distinguish action use from scientific quality."""
from amphora_contracts_research import (
    InterpretationMatchRecord,
    NormalizationTargetRecord,
    NormalizedMeasurementRecord,
    ObservationUseReviewRecord,
)

from .. import measurement_wire
from .. import wire as observation_wire
from .profiles import rule_to_wire


def normalization_to_wire(value):
    return NormalizedMeasurementRecord(original=measurement_wire.to_wire(value.original),
        targets=NormalizationTargetRecord(value_unit=value.targets.value_unit,coordinate_unit=value.targets.coordinate_unit),
        policy=value.policy,status=value.status,
        normalized=None if value.normalized is None else measurement_wire.to_wire(value.normalized),
        applied=tuple(rule_to_wire(rule) for rule in value.applied),reason=value.reason)


def match_to_wire(value):
    return InterpretationMatchRecord(disposition=value.disposition,reasons=value.reasons,state_bound=value.state_known)


def review_to_wire(value):
    return ObservationUseReviewRecord(observation=observation_wire.to_wire(value.observation),
        raw_match=match_to_wire(value.raw_match),effective_match=match_to_wire(value.match),
        normalization=None if value.normalization is None else normalization_to_wire(value.normalization),
        disposition=value.disposition,blockers=value.blockers,gaps=value.gaps,focus=value.focus)
