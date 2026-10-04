import copy
import time

import pytest
from amphora_agent_planning.campaign_research_access import (
    CampaignResearchWindow,
    ResearchRecordReader,
)
from amphora_agent_planning.research_access import ResearchReadWindow

from ..campaign_context.test_records import context, selected, values, wire

PATHS = {"question": "/v1/questions/read", "need": "/v1/evidence-needs/read", "assessment": "/v1/assessments/read"}


class Peer:
    def __init__(self):
        self.values = {path: wire(kind, values()[kind]) for kind, path in PATHS.items()}
        self.calls = []

    def read(self, path, reference, window):
        window.start()
        self.calls.append((path, reference))
        result = self.values[path]
        if callable(result):
            result = result(reference, window)
        if isinstance(result, Exception):
            raise result
        window.consume(len(result.model_dump_json().encode()))
        return result


def test_exact_public_read_routes_and_original_assessment_request():
    peer = Peer()
    report = ResearchRecordReader(peer).review(selected())
    assert report.context == context() and not report.failures
    assert report.calls == 3 and report.bytes > 0
    assert [path for path, _ in peer.calls] == list(PATHS.values())
    assert peer.calls[-1][1] == selected().document().assessments[0].request


@pytest.mark.parametrize("reason,gap", [("research_access_denied", "denied"),
    ("research_reference_unavailable", "unavailable"), ("research_peer_protocol", "unavailable")])
def test_per_record_failures_do_not_stop_other_available_lanes(reason, gap):
    peer = Peer()
    peer.values[PATHS["question"]] = ValueError(reason)
    report = ResearchRecordReader(peer).review(selected())
    assert report.calls == 3 and len(report.context.records) == 2
    assert report.context.gaps[0].reason == gap
    assert [item.code for item in report.failures] == [reason]
    assert {item.reason for item in report.context.findings} == {"question_unavailable"}


@pytest.mark.parametrize("reason", ["research_peer_unavailable", "research_read_expired", "research_read_byte_limit"])
def test_global_transport_failure_stops_remaining_calls_with_explicit_reasons(reason):
    peer = Peer()
    peer.values[PATHS["question"]] = ValueError(reason)
    report = ResearchRecordReader(peer).review(selected())
    assert report.calls == 1 and len(report.context.gaps) == 3 and not report.context.records
    assert [item.code for item in report.failures] == [reason] * 3


def test_actual_window_call_byte_and_deadline_exhaustion():
    peer, window = Peer(), CampaignResearchWindow()
    window.calls = 159
    report = ResearchRecordReader(peer).review(selected(), window)
    assert report.calls == 1 and len(peer.calls) == 1 and len(report.context.records) == 1
    assert [item.code for item in report.failures] == ["research_read_call_limit"] * 2
    peer, window = Peer(), CampaignResearchWindow()
    window.consumed = 4194303
    report = ResearchRecordReader(peer).review(selected(), window)
    assert report.calls == 1 and {item.code for item in report.failures} == {"research_read_byte_limit"}
    peer, window = Peer(), CampaignResearchWindow()
    window.deadline = time.monotonic() - 1
    report = ResearchRecordReader(peer).review(selected(), window)
    assert not peer.calls and report.calls == 0
    assert {item.code for item in report.failures} == {"research_read_expired"}


def test_reply_finishing_outside_window_is_not_usable_context():
    peer = Peer()
    response = peer.values[PATHS["question"]]

    def late(_reference, window):
        window.deadline = time.monotonic() - 1
        return response

    peer.values[PATHS["question"]] = late
    report = ResearchRecordReader(peer).review(selected())
    assert not report.context.records and report.calls == 1
    assert {item.code for item in report.failures} == {"research_read_expired"}


def test_response_for_another_selected_question_cannot_fill_the_wrong_read():
    peer = Peer()
    source = values()["question"]
    other = copy.deepcopy(source)
    other["reference"]["question_id"] = "second"
    choice = selected().document().model_dump(mode="json")
    choice["questions"].append(other["reference"])
    peer.values[PATHS["question"]] = wire("question", other)
    report = ResearchRecordReader(peer).review(selected(selection=choice))
    assert report.calls == 4 and len(report.failures) == 1
    assert report.failures[0].code == "research_record_binding"
    assert report.context.gaps[0].identity.document()["reference"] == source["reference"]
    assert report.context.records[0].document().reference.question_id == "second"


@pytest.mark.parametrize("variant", ["criteria", "wire", "digest"])
def test_invalid_records_fail_closed_with_safe_codes(variant):
    peer = Peer()
    if variant == "digest":
        status = values()["assessment"]
        status["outcome"]["assessment"]["sufficient"] = True
        peer.values[PATHS["assessment"]] = wire("assessment", status)
    else:
        question = peer.values[PATHS["question"]]
        peer.values[PATHS["question"]] = question.model_copy(update={"criteria": question.criteria * 2} if variant == "criteria" else
                                                            {"objective": None})
    report = ResearchRecordReader(peer).review(selected())
    assert len(report.context.records) == 2 and report.calls == 3
    assert report.failures[0].code == ("research_record_binding" if variant == "digest" else "research_record_invalid")


def test_pending_is_reported_as_owner_state_not_transport_failure():
    peer = Peer()
    value = values()["assessment"]
    value["outcome"] = {"status": "pending"}
    peer.values[PATHS["assessment"]] = wire("assessment", value)
    report = ResearchRecordReader(peer).review(selected())
    assert report.context.gaps[0].reason == "pending" and not report.failures


def test_unexpected_programming_errors_and_foreign_window_propagate():
    peer = Peer()
    peer.values[PATHS["question"]] = ValueError("unexpected_internal_error")
    with pytest.raises(ValueError, match="unexpected_internal_error"):
        ResearchRecordReader(peer).review(selected())
    with pytest.raises(ValueError, match="research_read_profile_mismatch"):
        ResearchRecordReader(peer).review(selected(), ResearchReadWindow())


def test_empty_selection_calls_nothing():
    choice = selected().document().model_dump(mode="json")
    for key in ("questions", "needs", "assessments"):
        choice[key] = []
    peer = Peer()
    report = ResearchRecordReader(peer).review(selected(selection=choice))
    assert report.calls == report.bytes == 0 and not peer.calls and not report.context.gaps
