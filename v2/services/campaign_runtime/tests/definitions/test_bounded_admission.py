"""Actual public admission and run-serialized capacity; synthetic tools only."""

import copy
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest

from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_campaign_runtime.completion.prepare import IntentPreparation
from amphora_campaign_runtime.completion.model import PreparedIntent
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.resource_profiles.preflight import require_supported_resources
from amphora_contracts_campaign_resources import parse_resource_bounded_draft
from amphora_contracts_commands import NUMERIC_ENCODING
from sqlalchemy import text
from fastapi.testclient import TestClient

from .test_eligibility_admission import eligible
from ..lifecycle.test_claims import command, run_row
from ..completion.test_preparation import Peer


def bounded(graph_env, monkeypatch, cap=1, *, admit=True):
    g, e = graph_env, graph_env.env
    for index in range(cap):
        second = copy.deepcopy(g.raw["body"]["nodes"][0])
        second["node_id"] = f"second-{index}"
        g.raw["body"]["nodes"].insert(1, second)
        g.raw["body"]["edges"].append({"source": second["node_id"], "target": "finish", "route": "next"})
    service, payload, calls, _ = eligible(g, monkeypatch)
    payload["budget"]["limit"] = cap + 10
    payload["resources"] = {"profile": "campaign-invocation-cap-v1", "max_active_attempts": cap}
    request = parse_resource_bounded_draft(json.dumps({"encoding": NUMERIC_ENCODING, "identity": {
        "scope": e.principal.scope.model_dump(), "actor_id": e.principal.actor_id,
        "command_family": "graph.admit_draft_bounded", "command_id": uuid.uuid4().hex}, "payload": payload}))
    receipt = service.admit_bounded_draft(e.principal, request) if admit else None
    if admit:
        assert receipt.outcome.status == "accepted", receipt
    return service, request, receipt, calls


def claim(e, run, key=None, tool=None):
    return RuntimeLeases(e.engine).claim(e.principal, command(e, "runtime.claim", {
        "run_id": run, "worker_id": e.principal.actor_id,
        "tool": tool or e.bounded_tool, "lease_seconds": 10}, key))


@pytest.mark.parametrize("cap", [1, 4, 8])
def test_concurrent_claims_replay_and_immutable_snapshot(graph_env, monkeypatch, cap):
    e = graph_env.env
    service, request, receipt, calls = bounded(graph_env, monkeypatch, cap)
    e.bounded_tool = graph_env.raw["body"]["nodes"][0]["tool"]
    run = receipt.outcome.committed.object_id
    keys = [f"claim-{index}" for index in range(cap + 1)]
    with ThreadPoolExecutor(max_workers=cap + 1) as pool:
        results = list(pool.map(lambda key: claim(e, run, key), keys))
    assert sorted(r.outcome.status for r in results) == ["claimed"] * cap + ["no_eligible_work"]
    row = run_row(e, run)
    assert (row["reserved"], row["spent"]) == (cap, 0)
    assert row["input_snapshot"]["resources"] == {"profile": "campaign-invocation-cap-v1", "max_active_attempts": cap}
    for key, expected in zip(keys, results):
        assert claim(e, run, key) == expected
    assert run_row(e, run)["revision"] == row["revision"]
    replacement = GraphAdmission(e.engine, PlanCatalog([]))
    assert replacement.admit_bounded_draft(e.principal, request) == receipt
    assert len(calls) == 1


def test_different_tool_poll_releases_vanished_worker_reservation(graph_env, monkeypatch):
    e = graph_env.env
    _, _, receipt, _ = bounded(graph_env, monkeypatch)
    e.bounded_tool = graph_env.raw["body"]["nodes"][0]["tool"]
    run = receipt.outcome.committed.object_id
    first = claim(e, run).outcome.invocation
    with e.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.attempts SET lease_expires_at=clock_timestamp()-interval '1 second' "
                          "WHERE run_id=:run AND attempt_id=:attempt"), {"run": run, "attempt": first.attempt_id})
    other = {**e.bounded_tool, "image_sha256": "d" * 64}
    assert claim(e, run, tool=other).outcome.status == "no_eligible_work"
    row = run_row(e, run)
    assert (row["reserved"], row["spent"]) == (0, 1)
    assert claim(e, run).outcome.status == "claimed"
    assert (run_row(e, run)["reserved"], run_row(e, run)["spent"]) == (1, 1)


def test_prepared_completion_keeps_capacity_until_reconciliation(graph_env, monkeypatch):
    e = graph_env.env
    _, _, receipt, _ = bounded(graph_env, monkeypatch)
    e.bounded_tool = graph_env.raw["body"]["nodes"][0]["tool"]
    run = receipt.outcome.committed.object_id
    first = claim(e, run).outcome.invocation
    output_type = graph_env.raw["body"]["outputs"][0]["value_type"]
    artifact = {"artifact_id": "result", "scope": e.principal.scope.model_dump(), "sha256": "e" * 64,
        "size_bytes": 30, "media_type": "application/json", "schema_ref": output_type["schema_ref"]}
    completion = command(e, "runtime.complete", {"run_id": run, "completion": {
        "schema_version": "1", "invocation_id": first.invocation_id,
        "attempt_id": first.attempt_id, "fence": first.fence,
        "outcome": {"status": "succeeded", "outputs": [{"port": "result", "artifact": artifact}]}}})
    preparation = IntentPreparation(e.engine, "runtime")
    assert isinstance(preparation.prepare(e.principal, completion), PreparedIntent)
    with e.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.attempts SET lease_expires_at=clock_timestamp()-interval '1 second' "
                          "WHERE run_id=:run"), {"run": run})
    blocked = claim(e, run, "at-capacity")
    assert blocked.outcome.status == "no_eligible_work"
    assert (run_row(e, run)["reserved"], run_row(e, run)["spent"]) == (1, 0)
    assert preparation.prepare(e.principal, completion).outcome.reason_code == "lease_expired"
    assert claim(e, run).outcome.status == "claimed"
    assert claim(e, run, "at-capacity") == blocked


@pytest.mark.parametrize("outcome,expected", [
    ({"status": "failed", "reason_code": "invalid", "retryable": False}, (0, 1)),
    ({"status": "uncertain_external_effect", "operation_id": "unknown", "reason_code": "uncertain"}, (1, 0)),
])
def test_failure_or_uncertainty_preserves_reservation_meaning(graph_env, monkeypatch, outcome, expected):
    e = graph_env.env
    _, _, receipt, _ = bounded(graph_env, monkeypatch)
    e.bounded_tool = graph_env.raw["body"]["nodes"][0]["tool"]
    run = receipt.outcome.committed.object_id
    first = claim(e, run).outcome.invocation
    completion = command(e, "runtime.complete", {"run_id": run, "completion": {
        "schema_version": "1", "invocation_id": first.invocation_id,
        "attempt_id": first.attempt_id, "fence": first.fence, "outcome": outcome}})
    service = CompletionCoordinator(e.engine, Peer())
    result = service.complete(e.principal, completion)
    assert result.outcome.status == "accepted", result
    assert service.complete(e.principal, completion) == result
    row = run_row(e, run)
    assert (row["reserved"], row["spent"]) == expected
    if expected[0]:
        assert claim(e, run).outcome.status == "rejected"
    else:
        assert claim(e, run).outcome.status == "claimed"


def test_cancel_settles_once_and_downgrade_preflight_rejects_active_cap(graph_env, monkeypatch):
    e = graph_env.env
    _, _, receipt, _ = bounded(graph_env, monkeypatch)
    e.bounded_tool = graph_env.raw["body"]["nodes"][0]["tool"]
    run = receipt.outcome.committed.object_id
    claim(e, run)
    with e.engine.connect() as conn:
        require_supported_resources(conn, "0.68.0")
        with pytest.raises(TransitionError, match="active_resource_profile_requires_runtime_0_68"):
            require_supported_resources(conn, "0.67.0")
    cancel = command(e, "runtime.cancel", {"run_id": run, "reason_code": "test_stop"})
    service = AuthorityCommands(e.engine)
    result = service.cancel(e.principal, cancel)
    assert result.outcome.status == "accepted", result
    assert service.cancel(e.principal, cancel) == result
    assert (run_row(e, run)["reserved"], run_row(e, run)["spent"]) == (0, 1)
    assert claim(e, run).outcome.status == "rejected"


def test_public_bounded_route_admits_and_rejects_invalid_capacity(graph_env, monkeypatch):
    e = graph_env.env
    service, request, _, calls = bounded(graph_env, monkeypatch, admit=False)
    app = create_app(e.service, e.credentials, graphs=(service, GraphAdvancer(e.engine)))
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer " + "x" * 32, "Content-Type": "application/json"}
        response = client.post("/v1/graph-drafts/admit-bounded", content=request.canonical_bytes, headers=headers)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["outcome"]["status"] == "accepted"
        run = result["outcome"]["committed"]["object_id"]
        assert run_row(e, run)["input_snapshot"]["resources"]["max_active_attempts"] == 1
        assert client.post("/v1/graph-drafts/admit-bounded", content=request.canonical_bytes, headers=headers).json() == result
        raw = json.loads(request.canonical_bytes)
        raw["identity"]["command_id"] = "invalid-cap"
        raw["payload"]["resources"]["max_active_attempts"] = 9
        assert client.post("/v1/graph-drafts/admit-bounded", json=raw, headers=headers).status_code == 422
    assert len(calls) == 1
