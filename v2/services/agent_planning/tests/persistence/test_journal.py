from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_agent_planning.providers import FixtureProvider, observe
from amphora_agent_planning.providers.capture import CapturedOutput, Observation
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def test_intent_pending_observation_and_replay(stored):
    s = stored
    ref = s.snapshot.document().reference
    assert s.journal.read_request(s.principal, ref) is None
    assert s.journal.read_attempt(s.principal, s.first.reference()) is None
    assert s.journal.register(s.principal, s.snapshot) == s.snapshot
    assert s.journal.register(s.principal, s.snapshot) == s.snapshot
    assert s.journal.read_request(s.principal, ref) == s.snapshot
    assert s.journal.read_attempt(s.principal, s.first.reference()) is None
    pending = s.journal.begin_attempt(s.principal, s.first)
    assert pending.observation is None
    assert s.journal.begin_attempt(s.principal, s.first) == pending
    observed = observe(s.first, FixtureProvider("abstain"))
    committed = s.journal.record(s.principal, s.first, observed)
    assert committed.observation == observed
    assert s.journal.record(s.principal, s.first, observed) == committed
    assert s.journal.begin_attempt(s.principal, s.first) == committed
    replacement = create_engine(s.engine.url)
    try:
        rebuilt = PlanningJournal(replacement)
        assert rebuilt.read_request(s.principal, ref) == s.snapshot
        assert rebuilt.read_attempt(s.principal, s.first.reference()) == committed
    finally:
        replacement.dispose()


def test_sequence_and_pending_are_not_success_or_free_retry(stored):
    s = stored
    with pytest.raises(ValueError, match="request_unknown"):
        s.journal.begin_attempt(s.principal, s.first)
    s.journal.register(s.principal, s.snapshot)
    with pytest.raises(ValueError, match="attempt_sequence"):
        s.journal.begin_attempt(s.principal, s.second)
    with pytest.raises(ValueError, match="attempt_unknown"):
        s.journal.record(s.principal, s.first, observe(s.first, FixtureProvider("abstain")))
    s.journal.begin_attempt(s.principal, s.first)
    with pytest.raises(ValueError, match="attempt_pending"):
        s.journal.begin_attempt(s.principal, s.second)
    unknown = observe(s.first, FixtureProvider("interrupted"))
    s.journal.record(s.principal, s.first, unknown)
    assert s.journal.begin_attempt(s.principal, s.second).observation is None
    assert s.journal.read_attempt(s.principal, s.first.reference()).observation.document().usage.input_tokens is None


def test_request_conflict_and_actor_scope_grants(stored):
    s = stored
    s.journal.register(s.principal, s.snapshot)
    altered = RequestSnapshot.bind(s.snapshot.document().model_copy(update={"decision_scope": "f" * 64}),
                                    actor_id=s.principal.actor_id, scope=s.principal.scope)
    other = AttemptBinding(altered, 1)
    for operation in [lambda: s.journal.register(s.principal, altered),
                      lambda: s.journal.begin_attempt(s.principal, other),
                      lambda: s.journal.read_attempt(s.principal, other.reference()),
                      lambda: s.journal.record(s.principal, other, observe(other, FixtureProvider("abstain")))]:
        with pytest.raises(ValueError, match="request_conflict"):
            operation()
    foreign = Principal("other", s.principal.scope, s.principal.actions)
    with pytest.raises(ValueError, match="request_actor_mismatch"):
        s.journal.read_request(foreign, s.snapshot.document().reference)
    denied = replace(s.principal, actions=frozenset())
    with pytest.raises(PermissionError, match="planning_access_denied"):
        s.journal.read_attempt(denied, s.first.reference())
    with pytest.raises(PermissionError, match="planning_access_denied"):
        s.journal.register(denied, s.snapshot)


@pytest.mark.parametrize("variant", ["proposal", "oversized", "malformed", "unknown_usage", "unavailable"])
def test_bounded_raw_output_and_usage_are_retained_separately(stored, variant):
    s = stored
    s.journal.register(s.principal, s.snapshot)
    s.journal.begin_attempt(s.principal, s.first)
    observation = observe(s.first, FixtureProvider(variant))
    s.journal.record(s.principal, s.first, observation)
    actual = s.journal.read_attempt(s.principal, s.first.reference()).observation
    assert actual.canonical == observation.canonical
    assert actual.capture == observation.capture
    assert b"capture_bytes" not in actual.canonical


def test_competing_observations_commit_exactly_one_immutable_history(stored):
    s = stored
    s.journal.register(s.principal, s.snapshot)
    barrier = Barrier(2)
    def begin():
        barrier.wait(5)
        return s.journal.begin_attempt(s.principal, s.first)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = [f.result(10) for f in [pool.submit(begin), pool.submit(begin)]]
    assert first == second
    barrier = Barrier(2)
    outcomes = [observe(s.first, FixtureProvider(v)) for v in ("abstain", "proposal")]
    def write(observation):
        barrier.wait(5)
        try:
            return s.journal.record(s.principal, s.first, observation)
        except ValueError as exc:
            return str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [f.result(10) for f in [pool.submit(write, item) for item in outcomes]]
    assert results.count("observation_conflict") == 1
    winner = next(result for result in results if not isinstance(result, str))
    assert s.journal.read_attempt(s.principal, s.first.reference()) == winner


def test_tampered_capture_does_not_commit(stored):
    s = stored
    s.journal.register(s.principal, s.snapshot)
    s.journal.begin_attempt(s.principal, s.first)
    observation = observe(s.first, FixtureProvider("abstain"))
    forged = Observation(CapturedOutput(b"forged", True), observation.canonical)
    with pytest.raises(ValueError, match="capture_digest_mismatch"):
        s.journal.record(s.principal, s.first, forged)
    assert s.journal.read_attempt(s.principal, s.first.reference()).observation is None


def test_service_database_role_cannot_rewrite_or_read_peer_tables(stored):
    s = stored
    for table in ["requests", "attempts", "observations"]:
        for sql in [f"DELETE FROM planning.{table} WHERE false", f"UPDATE planning.{table} SET tenant_id=tenant_id WHERE false"]:
            with pytest.raises(DBAPIError), s.engine.begin() as connection:
                connection.execute(text(sql))
    with pytest.raises(DBAPIError), s.engine.connect() as connection:
        connection.execute(text("SELECT * FROM knowledge.graph_profiles LIMIT 0"))
