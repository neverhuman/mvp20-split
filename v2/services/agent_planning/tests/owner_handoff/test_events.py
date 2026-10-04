import json

import pytest
from amphora_agent_planning.owner_handoff.events import HandoffEvent
from amphora_agent_planning.owner_handoff.receipt import OwnerOutcome
from amphora_agent_planning.publication.records import encode

from .test_values import accepted_fixture, request


def test_terminal_slot_survives_exhausted_retry_history():
    selected, _ = request()
    progress = HandoffEvent.record(selected, 1, "prepared").apply(None, selected, 1)
    for position in range(2, 64):
        progress = HandoffEvent.record(selected, position, "blocked", "owner_unavailable").apply(progress, selected, position)
    with pytest.raises(ValueError, match="handoff_terminal_slot_reserved"):
        HandoffEvent.record(selected, 64, "dispatch").apply(progress, selected, 64)
    receipt = OwnerOutcome.research(selected, selected.document())
    progress = HandoffEvent.record(selected, 64, "observed", json.loads(receipt.canonical)).apply(progress, selected, 64)
    assert progress.terminal and progress.state == "acknowledged"
    with pytest.raises(ValueError, match="handoff_terminal"):
        HandoffEvent.record(selected, 64, "observed", json.loads(receipt.canonical)).apply(progress, selected, 64)


def test_lost_write_stays_uncertain_and_forged_acceptance_fails():
    selected, status, accepted = accepted_fixture()
    progress = HandoffEvent.record(selected, 1, "prepared").apply(None, selected, 1)
    progress = HandoffEvent.record(selected, 2, "dispatch").apply(progress, selected, 2)
    progress = HandoffEvent.record(selected, 3, "uncertain").apply(progress, selected, 3)
    assert progress.state == "uncertain" and progress.dispatches == 1
    pending = OwnerOutcome.knowledge(selected, status)
    forged = json.loads(pending.canonical)
    forged["state"] = "acknowledged"
    with pytest.raises(ValueError, match="handoff_receipt_canonical"):
        OwnerOutcome.restore(selected, encode(forged))
    outcome = OwnerOutcome.knowledge(selected, status, accepted)
    assert OwnerOutcome.restore(selected, outcome.canonical) == outcome
    progress = HandoffEvent.record(selected, 4, "observed", json.loads(outcome.canonical)).apply(progress, selected, 4)
    assert progress.terminal and progress.dispatches == 1


@pytest.mark.parametrize("action,data", [("unknown", None), ("uncertain", None), ("blocked", "raw peer error"), ("dispatch", {})])
def test_illegal_transitions_are_not_outcomes(action, data):
    selected, _ = request()
    progress = HandoffEvent.record(selected, 1, "prepared").apply(None, selected, 1)
    with pytest.raises(ValueError):
        HandoffEvent.record(selected, 2, action, data).apply(progress, selected, 2)
