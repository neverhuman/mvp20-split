"""Occurrence-bound waits retain separate expectations through scatter and loop feedback."""

import copy
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.compiler import ToolCatalog
from amphora_campaign_runtime.coordinator import GraphAdmission, GraphReads, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.waits.coordinator import WaitCoordinator
from amphora_campaign_runtime.waits.reads import WaitReads
from amphora_contracts_campaigns import parse_executable_campaign
from export_schemas import ROOT
from sqlalchemy import text

from ..completion.test_acceptance import Peer
from .test_execution import submit_command


@pytest.mark.parametrize("case", [1, 2])
def test_nested_waits_preserve_member_order_and_loop_subject_feedback(graph_env, case):
    graph = graph_env
    raw = json.loads((ROOT / "contracts/fixtures/v3/await_cases.json").read_bytes())[case]["payload"]
    raw["scope"] = graph.env.principal.scope.model_dump(mode="json")
    if case == 2:
        raw["body"]["nodes"][0]["until"]["value"] = False
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), graph.source.schemas)
    assert PlanCatalog([entry]).needs_completion
    inputs = graph.payload["inputs"]
    if case == 1:
        items = [copy.deepcopy(inputs[0]["value"]) for _ in range(2)]
        for index, item in enumerate(items):
            item["artifact"]["artifact_id"] = f"subject-{index}"
        inputs = [{"port": "batch", "value": {"kind": "collection", "items": items}}]
    admitted = GraphAdmission(graph.env.engine, PlanCatalog([entry])).admit(graph.env.principal,
        graph.command("graph.admit", {"plan_sha256": entry.plan.sha256, "inputs": inputs, "budget": {"limit": 2}}))
    assert admitted.outcome.status == "accepted"
    run = admitted.outcome.committed.object_id
    issuer = replace(graph.env.principal, actor_id="synthetic-issuer", actions=frozenset({"submit_receipt", "read"}))
    subjects = {}
    accepted = []
    for _ in range(8):
        reply = GraphAdvancer(graph.env.engine).advance(graph.env.principal, graph.command("graph.advance", {"run_id": run}))
        assert reply.outcome.status == "accepted"
        page = GraphReads(graph.env.engine).run(graph.env.principal, run, version=2)
        if page.status != "running":
            break
        pending = sorted((node for node in page.nodes if node.kind == "await" and node.status == "issued"),
                         key=lambda node: node.path.occurrences[-1].index, reverse=True)
        for node in pending:
            index = node.path.occurrences[-1].index
            observed = WaitReads(graph.env.engine).observation(issuer, run, node.activation_id)
            subjects[index] = observed.expectation.subject.artifact_id
            f = SimpleNamespace(observation=observed, run=run, activation=node.activation_id)
            command = submit_command(f, mutate=lambda receipt, index=index:
                                     receipt["outcome"]["output"]["artifact"].update(artifact_id=f"out-{index}"))
            result = WaitCoordinator(graph.env.engine, Peer()).submit(issuer, command)
            assert result.outcome.status == "accepted"
            accepted.append(node.activation_id)
    assert page.status == "completed" and len(set(accepted)) == 2
    assert (page.spent, page.reserved) == (0, 0)
    with graph.env.engine.connect() as conn:
        outputs = conn.execute(text("SELECT outputs FROM runtime.graph_runs WHERE run_id=:run"), {"run": run}).scalar_one()
        assert conn.execute(text("SELECT count(*) FROM runtime.graph_wait_closures WHERE run_id=:run"), {"run": run}).scalar_one() == 2
    if case == 1:
        assert subjects == {0: "subject-0", 1: "subject-1"}
        assert [item["artifact"]["artifact_id"] for item in outputs[0]["value"]["items"]] == ["out-0", "out-1"]
    else:
        assert subjects == {0: "synthetic-input", 1: "out-0"}
        assert outputs[0]["value"]["artifact"]["artifact_id"] == "out-1"
