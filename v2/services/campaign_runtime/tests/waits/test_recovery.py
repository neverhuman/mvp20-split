"""Actual worker uncertainty and wait-intent cleanup preserve terminal run authority."""

from amphora_campaign_runtime.completion.artifacts import ReservationUnavailable
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.coordinator import GraphReads
from amphora_campaign_runtime.coordinator.polling import GraphPoller
from amphora_campaign_runtime.waits.coordinator import WaitCoordinator
from sqlalchemy import text

from ..completion.test_acceptance import Peer
from ..scheduling.test_advancement import claim
from .test_execution import observation, start, submit_command


def test_worker_uncertainty_does_not_strand_wait_retention_or_reopen_graph(graph_env):
    f = start(graph_env, mixed=True)
    class Unavailable(Peer):
        def reserve(self, reservation):
            raise ReservationUnavailable("lost_reply")
    command = submit_command(f)
    service = WaitCoordinator(graph_env.env.engine, Unavailable())
    assert service.submit(f.issuer, command).outcome.status == "pending"
    invocation = claim(graph_env, f.run)
    uncertain = graph_env.command("runtime.complete", {"run_id": f.run, "completion": {"schema_version": "1",
        "invocation_id": invocation.invocation_id, "attempt_id": invocation.attempt_id, "fence": invocation.fence,
        "outcome": {"status": "uncertain_external_effect", "operation_id": "unknown-effect", "reason_code": "uncertain"}}})
    assert CompletionCoordinator(graph_env.env.engine, Peer()).complete(graph_env.env.principal, uncertain).outcome.status == "accepted"
    reads = GraphReads(graph_env.env.engine)
    before = reads.run(graph_env.env.principal, f.run, version=2)
    assert before.status == "blocked" and (before.spent, before.reserved) == (0, 1)
    assert observation(f).closure is None
    poller = GraphPoller(graph_env.env.engine, f.advance)
    assert poller.tick(graph_env.env.principal)
    assert not poller.tick(graph_env.env.principal)
    after = reads.run(graph_env.env.principal, f.run, version=2)
    assert after.status == "blocked" and (after.spent, after.reserved) == (0, 1)
    assert observation(f).closure.outcome.status == "cancelled"
    assert service.submit(f.issuer, command).outcome.reason_code == "run_not_running"
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text("SELECT status FROM runtime.wait_retention_intents WHERE run_id=:run"),
                            {"run": f.run}).scalar_one() == "aborted"
