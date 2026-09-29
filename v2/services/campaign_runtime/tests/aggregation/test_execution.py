"""Real owner transactions; scripted Artifact peer proves only the retention client boundary."""

import pytest
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from sqlalchemy import text

from ..completion.test_acceptance import Peer
from ..scheduling.test_advancement import admit, advance, claim, complete, table


def partial(raw, minimum):
    node = next(node for node in raw["body"]["nodes"] if node["kind"] in {"join", "scatter"})
    node["policy"] = {"kind": "partial", "minimum": minimum, "close": "all_terminal"}
    node["output"]["value_type"]["missing_slots"] = True
    raw["body"]["outputs"][0]["value_type"]["missing_slots"] = True


def evidence(graph, run):
    with graph.env.engine.connect() as conn:
        return conn.execute(text("SELECT c.document AS cut,d.document AS decision,c.closure_revision,a.payload AS audit "
            "FROM runtime.graph_aggregate_cuts c JOIN runtime.graph_aggregate_decisions d "
            "USING(tenant_id,project_id,run_id,activation_id,cut_sha256) JOIN runtime.audit_events a "
            "ON a.tenant_id=c.tenant_id AND a.project_id=c.project_id AND a.run_id=c.run_id "
            "AND a.revision=c.closure_revision AND a.ordinal=0 WHERE c.run_id=:run"), {"run": run}).mappings().all()


@pytest.mark.parametrize("minimum,expected", [(1, "completed"), (2, "blocked")])
def test_partial_branch_join_commits_ordered_decision_with_audit(graph_env, minimum, expected):
    graph = graph_env
    inputs = [*graph.payload["inputs"], {"port": "flag", "value": {"kind": "boolean", "value": False}}]
    run = admit(graph, 1, inputs, modify=lambda raw: partial(raw, minimum))
    assert advance(graph, run).status == "running"
    assert evidence(graph, run) == []
    complete(graph, run, claim(graph, run), "right-result")
    assert advance(graph, run).status == expected
    stored = evidence(graph, run)[0]
    assert [member["status"] for member in stored["cut"]["members"]] == ["skipped", "succeeded"]
    assert stored["decision"]["eligible_members"] == ["right"]
    assert stored["audit"]["kind"] == "graph_advanced"
    if expected == "completed":
        values = stored["decision"]["collection"]["items"]
        assert values[0] == {"kind": "missing", "member_id": "left", "reason_code": "member_skipped"}
        assert values[1]["artifact"]["artifact_id"] == "right-result"
        assert table(graph, run, "graph_runs")[0]["outputs"][0]["value"] == stored["decision"]["collection"]
    else:
        assert stored["decision"]["reason_code"] == "aggregate_minimum_unmet"
        assert stored["decision"]["collection"] is None


def test_abstention_is_preserved_in_join_evidence(graph_env):
    graph = graph_env
    inputs = [*graph.payload["inputs"], {"port": "flag", "value": {"kind": "boolean", "value": True}}]
    run = admit(graph, 1, inputs, modify=lambda raw: partial(raw, 0))
    advance(graph, run)
    invocation = claim(graph, run)
    receipt = CompletionCoordinator(graph.env.engine, Peer()).complete(graph.env.principal,
        graph.command("runtime.complete", {"run_id": run, "completion": {"schema_version": "1",
            "invocation_id": invocation.invocation_id, "attempt_id": invocation.attempt_id, "fence": invocation.fence,
            "outcome": {"status": "abstained", "reason_code": "not_applicable"}}}))
    assert receipt.outcome.status == "accepted"
    page = advance(graph, run)
    assert page.status == "completed" and (page.spent, page.reserved) == (1, 0)
    stored = evidence(graph, run)[0]
    assert stored["cut"]["members"][0]["status"] == "abstained"
    assert stored["decision"]["collection"]["items"][0]["reason_code"] == "not_applicable"


def test_partial_scatter_minimum_does_not_close_at_first_completion(graph_env):
    graph = graph_env
    item = graph.payload["inputs"][0]["value"]
    run = admit(graph, 2, [{"port": "items", "value": {"kind": "collection", "items": [item, item]}}],
                modify=lambda raw: partial(raw, 1))
    advance(graph, run)
    first, second = claim(graph, run), claim(graph, run)
    complete(graph, run, second, "second")
    assert advance(graph, run).status == "running"
    assert evidence(graph, run) == []
    complete(graph, run, first, "first")
    assert advance(graph, run).status == "completed"
    stored = evidence(graph, run)[0]
    assert stored["decision"]["eligible_members"] == ["0", "1"]
    assert [v["artifact"]["artifact_id"] for v in stored["decision"]["collection"]["items"]] == ["first", "second"]


@pytest.mark.parametrize("minimum,expected", [(0, "completed"), (1, "blocked")])
def test_partial_empty_scatter_records_declared_minimum(graph_env, minimum, expected):
    graph = graph_env
    run = admit(graph, 2, [{"port": "items", "value": {"kind": "collection", "items": []}}],
                modify=lambda raw: partial(raw, minimum))
    assert advance(graph, run).status == expected
    stored = evidence(graph, run)[0]
    assert stored["cut"]["members"] == []
    assert stored["decision"]["eligible_members"] == []
