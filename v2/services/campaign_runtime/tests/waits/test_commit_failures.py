"""Interrupted acceptance and competing deliveries retain exactly one logical wait result."""

import pytest
from amphora_campaign_runtime.completion.artifacts import ReservationUnavailable
from amphora_campaign_runtime.waits.coordinator import WaitCoordinator
from sqlalchemy import text

from ..completion.test_acceptance import Peer
from .test_execution import observation, start, submit_command


def test_acceptance_rollback_keeps_prepared_protection_and_retry_uses_saved_reservation(graph_env, monkeypatch):
    f = start(graph_env)
    calls = []
    class CountingPeer(Peer):
        def reserve(self, reservation):
            calls.append(reservation)
            return super().reserve(reservation)
    service = WaitCoordinator(graph_env.env.engine, CountingPeer())
    command = submit_command(f)
    original = service.leases._changed
    def interrupt(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("after_wait_acceptance_writes")
    monkeypatch.setattr(service.leases, "_changed", interrupt)
    with pytest.raises(RuntimeError, match="after_wait_acceptance"):
        service.submit(f.issuer, command)
    assert observation(f).closure is None
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text("SELECT status FROM runtime.wait_retention_intents WHERE run_id=:run"),
                            {"run": f.run}).scalar_one() == "prepared"
        assert conn.execute(text("SELECT outputs FROM runtime.graph_nodes WHERE run_id=:run AND kind='await'"),
                            {"run": f.run}).scalar_one() is None
    assert WaitCoordinator(graph_env.env.engine, CountingPeer()).submit(f.issuer, command).outcome.status == "accepted"
    assert len(calls) == 1 and observation(f).closure.outcome.status == "accepted"


def test_competing_receipt_wins_while_first_reserves_and_loser_never_overwrites(graph_env):
    f = start(graph_env)
    winner = submit_command(f)
    class InterleavingPeer(Peer):
        def reserve(self, reservation):
            reply = WaitCoordinator(graph_env.env.engine, Peer()).submit(f.issuer, winner)
            assert reply.outcome.status == "accepted"
            return super().reserve(reservation)
    loser = submit_command(f)
    reply = WaitCoordinator(graph_env.env.engine, InterleavingPeer()).submit(f.issuer, loser)
    assert reply.outcome.status == "rejected" and reply.outcome.reason_code == "wait_already_closed"
    with graph_env.env.engine.connect() as conn:
        statuses = conn.execute(text("SELECT status FROM runtime.wait_retention_intents WHERE run_id=:run ORDER BY status"),
                                {"run": f.run}).scalars().all()
        assert statuses == ["aborted", "committed"]
        assert conn.execute(text("SELECT count(*) FROM runtime.graph_wait_closures WHERE run_id=:run"),
                            {"run": f.run}).scalar_one() == 1
    assert WaitCoordinator(graph_env.env.engine, Peer()).submit(f.issuer, winner).outcome.status == "accepted"


def test_bad_delivery_cannot_abort_another_commands_valid_preparation(graph_env):
    f = start(graph_env)
    class Unavailable(Peer):
        def reserve(self, reservation):
            raise ReservationUnavailable("lost_reply")
    valid = submit_command(f)
    assert WaitCoordinator(graph_env.env.engine, Unavailable()).submit(f.issuer, valid).outcome.status == "pending"
    invalid = submit_command(f, mutate=lambda raw: raw.update(purpose="wrong"))
    assert WaitCoordinator(graph_env.env.engine, Peer()).submit(f.issuer, invalid).outcome.reason_code == "wait_receipt_purpose_mismatch"
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text("SELECT status FROM runtime.wait_retention_intents WHERE run_id=:run"),
                            {"run": f.run}).scalar_one() == "prepared"
    assert WaitCoordinator(graph_env.env.engine, Peer()).submit(f.issuer, valid).outcome.status == "accepted"
