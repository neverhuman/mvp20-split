"""Pinned intake identity and lossless outcomes, including weak but useful reports."""
from dataclasses import replace

import pytest
from amphora_contracts_research import LabIntakeRequest
from amphora_research.observations.identity import ObservationError
from amphora_research.observations.intake import IntakeIntent
from amphora_research.observations.reports import ConfiguredLabReturn, ReconciledReport
from amphora_research.observations.resolution import ResolvedLabReport

from .test_reports import report_case


def intake_case():
    configured,experiment,source,report = report_case(True)
    request = LabIntakeRequest(wire_version="1",intake_id="intake",profile=configured.reference,report=source)
    intent = IntakeIntent.bind(configured,request,"fixture",source.scope)
    resolved = ResolvedLabReport(ReconciledReport.reconcile(configured,experiment,source,report),
        (source,report.raw_report,experiment.protocol.applicability,experiment.protocol.source))
    # Shared context fixtures may reference the same immutable Artifact.
    resolved = replace(resolved,inputs=tuple(dict.fromkeys(resolved.inputs)))
    return intent,resolved


def test_intent_rebuild_and_partial_terminal_preserve_exact_configuration():
    intent,resolved = intake_case()
    restored = IntakeIntent.restore(intent.content)
    assert restored == intent and restored.pending().outcome.status == "pending"
    terminal = restored.resolve(resolved)
    assert terminal.status.outcome.resolution.disposition == "partial"
    assert terminal.status.outcome.resolution.missing_expectations == ("second",)
    assert terminal.status.request == intent.request
    assert terminal.status.actor_id == "fixture"
    assert terminal == intent.resolve(replace(resolved,inputs=tuple(reversed(resolved.inputs))))


@pytest.mark.parametrize("change,reason",[
    (lambda i:i.request.model_copy(update={"profile":i.request.profile.model_copy(update={"sha256":"0"*64})}),"lab_intake_profile_mismatch"),
    (lambda i:i.request.model_copy(update={"report":i.request.report.model_copy(update={"scope":i.request.profile.scope.model_copy(update={"project_id":"other"})})}),"lab_intake_scope_mismatch"),
])
def test_intent_rejects_changed_profile_or_scope(change,reason):
    intent,_ = intake_case()
    with pytest.raises(ObservationError,match=reason):
        IntakeIntent.bind(intent.configured,change(intent),intent.actor,intent.request.profile.scope)


def test_full_configuration_changes_digest_even_with_same_profile_label():
    intent,_ = intake_case()
    changed = ConfiguredLabReturn(intent.configured.document.model_copy(update={"publishers":("different",)}))
    assert changed.reference.profile_id == intent.request.profile.profile_id
    assert changed.reference.sha256 != intent.request.profile.sha256


@pytest.mark.parametrize("change,reason",[
    (lambda r:replace(r,inputs=()),"lab_intake_input_limit"),
    (lambda r:replace(r,inputs=r.inputs+r.inputs[:1]),"lab_intake_input_duplicate"),
    (lambda r:replace(r,inputs=r.inputs[1:]),"lab_intake_input_missing"),
    (lambda r:replace(r,report=replace(r.report,source=r.report.raw_report)),"lab_intake_resolution_mismatch"),
    (lambda r:replace(r,inputs=(r.inputs[0].model_copy(update={"scope":r.inputs[0].scope.model_copy(update={"project_id":"other"})}),)),"lab_intake_input_scope"),
])
def test_invalid_terminal_cannot_be_bound(change,reason):
    intent,resolved = intake_case()
    with pytest.raises(ObservationError,match=reason):
        intent.resolve(change(resolved))


def test_explicit_operational_failure_contains_no_negative_scientific_verdict():
    intent,_ = intake_case()
    terminal = intent.fail("malformed_report")
    assert terminal.status.outcome.status == "failed" and terminal.inputs == ()
    assert "resolution" not in terminal.status.outcome.model_dump()
