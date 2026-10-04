"""Coordinator failure/authority choices; actual owner I/O has its separate probe."""

from types import SimpleNamespace

import pytest
from amphora_agent_planning.repair.runner import RepairInputUnavailable
from amphora_agent_planning.result_publication.diagnostics import NoRepairNeeded
from amphora_agent_planning.result_publication.producer import DiagnosticProducer
from amphora_tool_protocol import TransportLost

from .test_preparation import preparation


def producer(status="unknown", fault=None):
    test = preparation()
    calls = []
    stored = SimpleNamespace(projection=SimpleNamespace(document=lambda: SimpleNamespace(outcome=SimpleNamespace(status=status))))
    def read(principal, reference):
        calls.append("owned_read")
        assert reference == test.history.projection.reference()
        return stored
    state = SimpleNamespace(attempt=SimpleNamespace(stage="finalized", result=SimpleNamespace(artifact="interpretation")))
    def publish(*_):
        calls.append("publish")
        if fault is not None:
            raise fault
        return state
    traces = SimpleNamespace(journal=SimpleNamespace(store=SimpleNamespace(extractions=SimpleNamespace(read_trace=read))), publish=publish)
    result = SimpleNamespace(journal=SimpleNamespace(store=SimpleNamespace(publisher_id="data-owner")), publish=publish)
    from amphora_agent_planning.access import Principal
    principal = Principal("fixture", test.case.scope, frozenset({"record_attempts", "read_attempts"}))
    return DiagnosticProducer(principal, traces, result), test, calls, state


@pytest.mark.parametrize("status", ["abstained", "policy_rejected"])
def test_owned_terminal_state_overrides_caller_step_status_without_publication(status):
    subject, test, calls, _ = producer(status)
    step = SimpleNamespace(trace=test.history.projection, stop_reason="proposed")
    assert subject.next(step) is None
    assert calls == ["owned_read"]


@pytest.mark.parametrize("fault,reason", [
    (TransportLost("private transport text"), "diagnostic_publication_uncertain"),
    (ValueError("private candidate data / secret"), "repair_input_unavailable"),
    (PermissionError("source_access_denied"), "source_access_denied"),
])
def test_failed_publication_retains_safe_distinct_stop_reasons(fault, reason):
    subject, test, calls, _ = producer(fault=fault)
    with pytest.raises(RepairInputUnavailable) as caught:
        subject.produce(test.history.projection.reference())
    assert caught.value.reason == reason and calls == ["owned_read", "publish"]


def test_no_repair_is_not_reported_as_input_failure():
    subject, test, _, _ = producer(fault=NoRepairNeeded("diagnostic_no_structural_repair"))
    assert subject.produce(test.history.projection.reference()) is None


def test_interpretation_rejection_prevents_dependent_result_publication():
    subject, test, calls, state = producer()
    state.attempt.stage = "rejected"
    with pytest.raises(RepairInputUnavailable, match="diagnostic_interpretation_rejected"):
        subject.produce(test.history.projection.reference())
    assert calls == ["owned_read", "publish"]


@pytest.mark.parametrize("stage", ["finalized", "rejected"])
def test_result_receipt_is_required_before_returning_repair_inputs(stage):
    subject, test, calls, _ = producer()
    artifact = test.history.interpretation.attempt.result.artifact
    def publish(principal, selection):
        calls.append("result")
        assert selection.trace() == test.history.projection.reference()
        return SimpleNamespace(attempt=SimpleNamespace(stage=stage, result=SimpleNamespace(artifact=artifact)))
    subject.results.publish = publish
    if stage == "rejected":
        with pytest.raises(RepairInputUnavailable, match="diagnostic_feedback_rejected"):
            subject.produce(test.history.projection.reference())
    else:
        result = subject.produce(test.history.projection.reference())
        assert result.parent == test.history.projection.reference() and result.feedback == artifact
    assert calls == ["owned_read", "publish", "result"]
