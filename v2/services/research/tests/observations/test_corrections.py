"""Corrections retain old values/bindings and explicitly target future selection."""
from dataclasses import replace

import pytest
from amphora_research.observations.corrections import ObservationCorrection
from amphora_research.observations.records import ReportedQuality

from .test_matching import observation


def test_immediate_correction_keeps_original_and_reports_only_changed_fields():
    before = observation()
    after = replace(before,identity=replace(before.identity,reference=replace(before.identity.reference,revision=2),
        supersedes=before.identity.reference),quality=ReportedQuality("failed",("low_accuracy",)))
    transition = ObservationCorrection(before,after)
    assert transition.policy == "future_campaigns_only" and transition.changed_fields == ("quality",)
    assert transition.before.quality.controls == "unknown" and transition.after.quality.controls == "failed"
    with pytest.raises(ValueError,match="predecessor_mismatch"):
        ObservationCorrection(after,before)
    no_change = replace(after,quality=before.quality)
    assert ObservationCorrection(before,no_change).changed_fields == ()
