"""Publication fencing, stable identities, ancestry and ambiguous-stream boundaries."""

import pytest
from amphora_contracts_population import candidate_birth_schema
from amphora_evolution_search.population import NumericBirth
from amphora_tool_protocol import ProtocolError


def test_publication_deduplicates_parents_and_reuses_exact_label(worker_artifacts):
    e = worker_artifacts
    record = NumericBirth.seed(e.original, 0).record
    first = e.session.publish(record, candidate_birth_schema(), (e.source, e.source), "birth/0")
    assert e.session.publish(record, candidate_birth_schema(), (e.source,), "birth/0") == first
    assert [call[0] for call in e.client.calls] == ["begin", "stream", "finalize"]
    assert e.client.parents[first.reference.artifact_id] == (e.source,)
    assert e.attempt.refreshes == 3
    with pytest.raises(ValueError, match="label_conflict"):
        e.session.publish(NumericBirth.seed(e.original, 1).record, candidate_birth_schema(), (e.source,), "birth/0")


def test_ambiguous_stream_never_finalizes_or_retries(worker_artifacts):
    e = worker_artifacts
    e.client.stream_failure = True
    with pytest.raises(ProtocolError):
        e.session.publish(NumericBirth.seed(e.original, 0).record, candidate_birth_schema(), (e.source,), "birth/0")
    assert [call[0] for call in e.client.calls] == ["begin", "stream"]
    assert e.session.published == {}


def test_lost_authority_prevents_any_publication(worker_artifacts):
    e = worker_artifacts
    e.attempt.live = False
    with pytest.raises(ProtocolError):
        e.session.publish(NumericBirth.seed(e.original, 0).record, candidate_birth_schema(), (e.source,), "birth/0")
    assert e.client.calls == []


def test_conflicting_parent_alias_rejects_before_io(worker_artifacts):
    e = worker_artifacts
    changed = e.source.model_copy(update={"sha256": "f" * 64})
    with pytest.raises(ValueError, match="parent_conflict"):
        e.session.publish(NumericBirth.seed(e.original, 0).record, candidate_birth_schema(), (e.source, changed), "birth/0")
    assert e.client.calls == []
