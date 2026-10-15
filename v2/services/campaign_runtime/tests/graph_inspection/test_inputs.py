"""Approved original-input observation through actual owner state and HTTP grants."""
import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.execution_proofs.reads import ExecutionProofs
from amphora_campaign_runtime.graph_inspection.inputs import InputObservationError, NodeInputs
from amphora_campaign_runtime.inspection.cursors import InspectionError
from amphora_campaign_runtime.inspection.history import RuntimeHistory
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_core import Scope
from fastapi.testclient import TestClient
from sqlalchemy import event, text

from ..completion.test_acceptance import Peer
from ..scheduling.test_advancement import admit, advance, claim, complete, table
from .test_snapshots import start


def inspector(graph):
    return replace(graph.env.principal, actions=graph.env.principal.actions | {"inspect_receipts"})


def test_queued_success_inputs_and_original_scope_survive_progress(graph_env):
    g = graph_env; run, _, snapshots = start(g); p = inspector(g)
    queued = next(row for row in table(g, run, "activations"))
    reads = NodeInputs(g.env.engine)
    before = reads.read(p, run, queued["activation_id"])
    assert before.invocation is not None
    assert before.scope_inputs[0].artifact.artifact_id == "synthetic-input"
    inv = claim(g, run)
    command, receipt = complete(g, run, inv)
    advance(g, run)
    after = NodeInputs(g.env.engine).read(p, run, inv.activation_id)
    assert after.invocation == before.invocation
    assert after.scope_inputs == before.scope_inputs
    assert after.observed_run_revision > before.observed_run_revision
    proof = ExecutionProofs(g.env.engine).read(p, run, receipt.outcome.committed.object_id)
    assert proof.invocation == after.invocation
    assert not {"fence", "lease_expires_at", "grant_id", "worker_id"} & set(json.loads(after.invocation.model_dump_json()))


@pytest.mark.parametrize("retryable", [True, False])
def test_failed_inputs_remain_available_without_changing_producer_semantics(graph_env, retryable):
    g = graph_env; run, _, _ = start(g); p = inspector(g); inv = claim(g, run)
    before = NodeInputs(g.env.engine).read(p, run, inv.activation_id)
    receipt = CompletionCoordinator(g.env.engine, Peer()).complete(g.env.principal, g.command("runtime.complete", {
        "run_id": run, "completion": {"schema_version":"1", "invocation_id":inv.invocation_id,
            "attempt_id":inv.attempt_id,"fence":inv.fence,
            "outcome":{"status":"failed","reason_code":"fixture_failure","retryable":retryable}}}))
    assert receipt.outcome.status == "accepted"
    assert NodeInputs(g.env.engine).read(p, run, inv.activation_id).invocation == before.invocation
    with pytest.raises(InspectionError, match="producer_unavailable"):
        ExecutionProofs(g.env.engine).read(p, run, receipt.outcome.committed.object_id)


def test_skipped_and_unmaterialized_nodes_expose_original_containing_scope_only(graph_env):
    g = graph_env
    run = admit(g, 1, [*g.payload["inputs"], {"port":"flag","value":{"kind":"boolean","value":True}}])
    advance(g, run)
    skipped = next(row for row in table(g, run, "graph_nodes") if row["status"] == "skipped")
    result = NodeInputs(g.env.engine).read(inspector(g), run, skipped["activation_id"])
    assert result.invocation is None
    flag = next(item for item in result.scope_inputs if item.port == "flag")
    assert flag.kind == "boolean" and flag.item_count == 1 and flag.artifact is None
    assert "value" not in flag.model_dump()


def test_each_grant_scope_and_node_identity_required(graph_env):
    g=graph_env; run,_,_=start(g); p=inspector(g)
    node=table(g,run,"graph_nodes")[0]["activation_id"]; reads=NodeInputs(g.env.engine)
    for action in ("read","inspect_receipts"):
        with pytest.raises(TransitionError,match="access_denied"):
            reads.read(replace(p,actions=p.actions-{action}),run,node)
    other=replace(p,scope=Scope(tenant_id=p.scope.tenant_id,project_id="other"))
    with pytest.raises(InspectionError,match="run_unavailable"): reads.read(other,run,node)
    with pytest.raises(InspectionError,match="graph_node_unavailable"): reads.read(p,run,"f"*64)


def test_only_readonly_sql_and_no_owner_state_changes(graph_env):
    g=graph_env;run,_,_=start(g);node=table(g,run,"graph_nodes")[0]["activation_id"]
    statements=[]
    def observed(_conn,_cursor,statement,*_args): statements.append(statement)
    event.listen(g.env.engine,"before_cursor_execute",observed)
    try: NodeInputs(g.env.engine).read(inspector(g),run,node)
    finally: event.remove(g.env.engine,"before_cursor_execute",observed)
    assert statements[0] == "SET TRANSACTION READ ONLY"
    assert all(s.startswith(("SELECT ","SET TRANSACTION READ ONLY")) for s in statements)


def test_malformed_retained_scope_fails_closed_without_editing_immutable_owner_state(graph_env):
    from amphora_campaign_runtime.graph_inspection.inputs import RetainedInputs
    g=graph_env
    corrupt=json.loads(json.dumps(g.payload["inputs"]))
    corrupt[0]["value"]["artifact"]["scope"]["project_id"]="other"
    with pytest.raises(InputObservationError):
        RetainedInputs.load({"scope_inputs":corrupt,"specification":None,"invocation_id":None},g.env.principal.scope)


def test_expired_attempt_and_worker_revocation_do_not_remove_retained_inputs(graph_env):
    from ..lifecycle.test_settlement import expire
    from amphora_campaign_runtime.lifecycle.settlement import BudgetSettlement
    g=graph_env;run,_,_=start(g);p=inspector(g);inv=claim(g,run)
    before=NodeInputs(g.env.engine).read(p,run,inv.activation_id)
    expire(g.env,run)
    BudgetSettlement(g.env.engine).sweep(g.env.principal,run)
    revoker=replace(g.env.principal,actions=g.env.principal.actions|{"revoke"})
    AuthorityCommands(g.env.engine).revoke(revoker,g.command("runtime.revoke_worker",
        {"worker_id":g.env.principal.actor_id,"reason_code":"fixture_revocation"}))
    after=NodeInputs(g.env.engine).read(p,run,inv.activation_id)
    assert after.invocation==before.invocation and after.scope_inputs==before.scope_inputs
    assert after.observed_run_revision>before.observed_run_revision


def test_http_no_store_grants_and_unconfigured_route_absence(graph_env):
    g=graph_env;run,cursors,_=start(g);p=inspector(g)
    node=table(g,run,"graph_nodes")[0]["activation_id"]
    credentials=RuntimeCredentials([("q"*32,p),("r"*32,g.env.principal)])
    graphs=g.admission,GraphAdvancer(g.env.engine)
    assert not any(path.endswith("/inputs") for path in create_app(g.env.service,credentials,graphs=graphs).openapi()["paths"])
    app=create_app(g.env.service,credentials,graphs=graphs,history=RuntimeHistory(g.env.engine,cursors))
    path=f"/v1/graph-observations/{run}/nodes/{node}/inputs"
    with TestClient(app) as client:
        for token,status in [(None,401),("r"*32,403),("q"*32,200)]:
            response=client.get(path,headers={"Authorization":"Bearer "+token} if token else {})
            assert response.status_code==status, response.text
            assert response.headers["cache-control"]=="no-store"
        response=client.get(path.replace(node,"f"*64),headers={"Authorization":"Bearer "+"q"*32})
        assert response.status_code==404 and response.headers["cache-control"]=="no-store"
