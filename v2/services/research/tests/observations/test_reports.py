"""Return coverage, missing values and quality remain separate during reconciliation."""
import hashlib
from dataclasses import replace

import pytest
from amphora_contracts_research import (
    LabReturnProfile,
    MissingMeasurement,
    ObservationQuality,
    ReportedObservation,
    SyntheticLabReport,
    synthetic_lab_report_schema,
)
from amphora_research.experiments.wire import reference_to_wire
from amphora_research.observations.identity import ObservationError
from amphora_research.observations.report_wire import to_resolution
from amphora_research.observations.reports import ConfiguredLabReturn, ReconciledReport
from amphora_research.observations.wire import to_wire

from ..experiments.fixtures import experiment
from ..material_state.test_context import METHOD, OTHER, artifact
from .test_matching import observation


def report_case(two=False):
    plan = experiment()
    if two:
        next_expected = replace(plan.expectations[0],expectation_id="second",replicate=replace(plan.expectations[0].replicate,replicate_id="replicate-2"))
        plan = replace(plan,expectations=plan.expectations+(next_expected,))
    configured = ConfiguredLabReturn(LabReturnProfile(wire_version="1",authority="synthetic",profile_id="lab",version="1",
        experiment=reference_to_wire(plan.identity.reference),adapter=METHOD,publishers=("fixture",)))
    original = to_wire(observation(plan))
    row = ReportedObservation(reference=original.reference,supersedes=original.supersedes,
        binding=original.binding,value=original.value,quality=original.quality)
    report = SyntheticLabReport(wire_version="1",authority="synthetic",issuer="fixture",adapter=METHOD,raw_report=artifact("raw"),observations=(row,))
    content = report.model_dump_json().encode()
    source = artifact("parsed-report").model_copy(update={"schema_ref":synthetic_lab_report_schema(),
        "sha256":hashlib.sha256(content).hexdigest(),"size_bytes":len(content)})
    return configured,plan,source,report


def test_partial_return_preserves_useful_result_and_exact_missing_expectation():
    configured,plan,source,report = report_case(True)
    result = ReconciledReport.reconcile(configured,plan,source,report)
    assert result.disposition == "partial" and result.missing_expectations == ("second",)
    assert result.entries[0].observation.source == source and result.entries[0].match.disposition == "matched"
    output = to_resolution(result)
    assert output.missing_expectations == ("second",) and output.authority == "synthetic"


def test_return_coverage_does_not_hide_missing_measurements_or_failed_controls():
    configured,plan,source,report = report_case()
    row = report.observations[0].model_copy(update={"value":MissingMeasurement(kind="missing",reason="not_reported"),
        "quality":ObservationQuality(controls="failed",flags=("questionable",))})
    result = ReconciledReport.reconcile(configured,plan,source,report.model_copy(update={"observations":(row,)}))
    assert result.disposition == "complete" and not result.missing_expectations
    assert result.unavailable_values == (result.entries[0].observation.identity.reference,)
    assert result.entries[0].observation.quality.controls == "failed"
    assert to_resolution(result).unavailable_values == (row.reference,)


def test_unmatched_and_empty_returns_remain_explicit():
    configured,plan,source,report = report_case()
    wrong = report.observations[0].model_copy(update={"binding":report.observations[0].binding.model_copy(update={
        "role":"blank"})})
    for rows in ((),(wrong,)):
        result = ReconciledReport.reconcile(configured,plan,source,report.model_copy(update={"observations":rows}))
        assert result.disposition == "unmatched" and result.missing_expectations == ("readout",)
    assert result.entries[0].match.reasons == ("control_role_mismatch",)
    assert result.entries[0].observation.value.quantity.value.text == "1.25"


def test_conflicting_replicate_results_are_not_averaged_or_deduplicated():
    configured,plan,source,report = report_case()
    first = report.observations[0]
    second = first.model_copy(update={"reference":first.reference.model_copy(update={"observation_id":"other-result"}),
        "value":first.value.model_copy(update={"quantity":first.value.quantity.model_copy(update={"value":"99"})})})
    result = ReconciledReport.reconcile(configured,plan,source,report.model_copy(update={"observations":(first,second)}))
    assert result.disposition == "complete" and len(result.entries) == 2
    assert [e.observation.value.quantity.value.text for e in result.entries] == ["1.25","99"]


@pytest.mark.parametrize("field,change,reason",[
    ("configured",lambda c,p,s,r: None,"lab_reconciliation_context_required"),
    ("source",lambda c,p,s,r: None,"lab_report_required"),
    ("configured",lambda c,p,s,r: ConfiguredLabReturn(c.document.model_copy(update={"experiment":c.document.experiment.model_copy(update={"revision":2})})),"lab_experiment_revision_mismatch"),
    ("source",lambda c,p,s,r: s.model_copy(update={"scope":OTHER}),"lab_report_scope_mismatch"),
    ("report",lambda c,p,s,r: r.model_copy(update={"raw_report":artifact(scope=OTHER)}),"lab_report_scope_mismatch"),
    ("report",lambda c,p,s,r: r.model_copy(update={"adapter":METHOD.model_copy(update={"version":"2"})}),"lab_adapter_mismatch"),
    ("report",lambda c,p,s,r: r.model_copy(update={"issuer":"unknown"}),"lab_issuer_not_configured"),
    ("report",lambda c,p,s,r: r.model_copy(update={"observations":r.observations*2}),"duplicate_lab_observation"),
    ("report",lambda c,p,s,r: r.model_copy(update={"observations":(r.observations[0].model_copy(update={"reference":r.observations[0].reference.model_copy(update={"scope":OTHER})}),)}),"lab_observation_scope_mismatch"),
])
def test_invalid_owner_context_cannot_be_reconciled(field,change,reason):
    values = report_case()
    args = dict(zip(("configured","experiment","source","report"),values,strict=True))
    args[field] = change(*values)
    with pytest.raises(ObservationError,match=reason):
        ReconciledReport.reconcile(**args)


def test_profile_requires_valid_unique_publishers():
    with pytest.raises(ObservationError,match="lab_profile_required"):
        ConfiguredLabReturn(None)
    configured,*_ = report_case()
    with pytest.raises(ObservationError,match="duplicate_lab_publisher"):
        ConfiguredLabReturn(configured.document.model_copy(update={"publishers":("fixture","fixture")}))
