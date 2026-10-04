from dataclasses import replace

import pytest
from amphora_agent_planning.owner_handoff.history import HandoffHistory
from amphora_agent_planning.owner_handoff.selection import HandoffSelection
from amphora_agent_planning.result_publication.history import ResultHistory

from ..publication.test_journal import setup
from ..result_publication.test_history import finalize


@pytest.mark.postgres
def test_handoff_uses_same_owned_origin_without_write_grant(stored):
    journal, result, _ = finalize(stored)
    selection = HandoffSelection.bind(stored.principal, result.trace(), "publication", "question", "q", "research")
    reader = replace(stored.principal, actions=frozenset({"read_attempts"}))
    with stored.engine.begin() as connection:
        history = HandoffHistory.load(connection, reader, selection, journal)
        original = ResultHistory.load(connection, reader, result, journal)
    assert history.task == original.task
    assert history.projection == original.projection
    assert history.observation == original.observation
    assert history.prior == original.prior
    assert history.interpretation == original.interpretation


@pytest.mark.postgres
@pytest.mark.parametrize("fault", ["trace", "interpretation", "actor"])
def test_handoff_cannot_substitute_unowned_origin(stored, fault):
    journal, result, _ = finalize(stored)
    principal = replace(stored.principal, actor_id="other") if fault == "actor" else stored.principal
    trace = result.trace().model_copy(update={"trace_id": "unknown"}) if fault == "trace" else result.trace()
    interpretation = "unknown" if fault == "interpretation" else "publication"
    selection = HandoffSelection.bind(principal, trace, interpretation, "question", "q", "research")
    with stored.engine.begin() as connection, pytest.raises(ValueError):
        HandoffHistory.load(connection, principal, selection, journal)


@pytest.mark.postgres
def test_handoff_requires_finalized_interpretation(stored):
    _, journal, identity, _, _ = setup(stored)
    selection = HandoffSelection.bind(stored.principal, identity.trace(), "publication", "question", "q", "research")
    with stored.engine.begin() as connection, pytest.raises(ValueError, match="interpretation_not_published"):
        HandoffHistory.load(connection, stored.principal, selection, journal)
