"""Retry history is bounded and distinguishes reports from canonical accepted results."""

import pytest
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.graph_inspection.details import GraphDetails
from amphora_campaign_runtime.inspection.cursors import InspectionError

from ..completion.test_acceptance import Peer
from ..scheduling.test_advancement import advance, claim, complete
from .test_snapshots import start


def test_attempt_pages_preserve_retry_report_and_canonical_completion(graph_env):
    graph = graph_env
    run, cursors, snapshots = start(graph)
    first = claim(graph, run)
    failed = CompletionCoordinator(graph.env.engine, Peer()).complete(graph.env.principal, graph.command("runtime.complete", {
        "run_id": run, "completion": {"schema_version": "1", "invocation_id": first.invocation_id, "attempt_id": first.attempt_id,
            "fence": first.fence, "outcome": {"status": "failed", "reason_code": "retry_fixture", "retryable": True}}}))
    assert failed.outcome.status == "accepted"
    second = claim(graph, run)
    complete(graph, run, second)
    advance(graph, run)
    snapshot = snapshots.page(graph.env.principal, run)
    details = GraphDetails(graph.env.engine, cursors)
    page1 = details.node(graph.env.principal, run, first.activation_id, snapshot_token=snapshot.snapshot.snapshot_token, limit=1)
    page2 = details.node(graph.env.principal, run, first.activation_id, snapshot_token=snapshot.snapshot.snapshot_token,
        limit=1, cursor=page1.next_cursor)
    assert page1.attempts[0].attempt_id == first.attempt_id and not page1.attempts[0].canonical_result
    assert page1.attempts[0].completion_id == failed.outcome.committed.object_id
    assert page2.attempts[0].attempt_id == second.attempt_id and page2.attempts[0].canonical_result
    assert page2.next_cursor is None and page1.cut == page2.cut
    other = next(node.activation_id for node in snapshot.nodes if node.activation_id != first.activation_id)
    with pytest.raises(InspectionError, match="cursor_mismatch"):
        details.node(graph.env.principal, run, other, snapshot_token=snapshot.snapshot.snapshot_token, cursor=page1.next_cursor)
    with pytest.raises(InspectionError, match="graph_output_unavailable"):
        details.values(graph.env.principal, run, other, "absent", snapshot_token=snapshot.snapshot.snapshot_token)
