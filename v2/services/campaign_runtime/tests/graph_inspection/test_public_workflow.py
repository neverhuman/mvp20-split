"""Public ASGI handlers and real PostgreSQL; only the external Artifact peer is scripted."""

import copy
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.coordinator import GraphAdmission, GraphAdvancer, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.inspection.cursors import CursorCodec
from amphora_campaign_runtime.inspection.history import RuntimeHistory
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from fastapi.testclient import TestClient
from sqlalchemy import text

from ..compiler.conftest import definition
from ..completion.test_acceptance import Peer


class ConcurrentReservations(Peer):
    def __init__(self):
        self.barrier = threading.Barrier(2)
        self.prepared = []

    def reserve(self, reservation):
        self.prepared.append(reservation.intent.intent_id)
        self.barrier.wait(timeout=10)
        return super().reserve(reservation)


def test_parallel_public_completions_preserve_history_and_resnapshot_failures(graph_env):
    graph = graph_env
    raw = copy.deepcopy(graph.source.raw[2])
    raw["scope"] = graph.env.principal.scope.model_dump(mode="json")
    entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
    admission = GraphAdmission(graph.env.engine, PlanCatalog([entry]))
    clock = [1000]
    cursors = CursorCodec("public-workflow-observation-key-" * 2, clock=lambda: clock[0], ttl_seconds=60)
    peer = ConcurrentReservations()
    denied = replace(graph.env.principal, actions=frozenset())
    credentials = RuntimeCredentials([("g" * 32, graph.env.principal), ("d" * 32, denied)])
    app = create_app(graph.env.service, credentials, completion=CompletionCoordinator(graph.env.engine, peer),
        graphs=(admission, GraphAdvancer(graph.env.engine)), history=RuntimeHistory(graph.env.engine, cursors))
    headers = {"Authorization": "Bearer " + "g" * 32}
    with TestClient(app) as client:
        def post(path, command):
            response = client.post(path, headers=headers, json=json.loads(command.canonical_bytes))
            assert response.status_code == 200, response.json()
            return response.json()

        def get(path, **params):
            response = client.get(path, headers=headers, params=params)
            assert response.status_code == 200, response.json()
            return response.json()

        payload = {"plan_sha256": entry.plan.sha256, "budget": {"limit": 8}, "inputs": [{"port": "items", "value": {
            "kind": "collection", "items": [graph.payload["inputs"][0]["value"]] * 2}}]}
        admitted = post("/v1/graph-runs", graph.command("graph.admit", payload))
        assert admitted["outcome"]["status"] == "accepted"
        run = admitted["outcome"]["committed"]["object_id"]
        path = "/v1/graph-observations/" + run
        initial = get(path + "/nodes", limit=1)
        rejected = post("/v1/graph-runs", graph.command("graph.admit", payload))
        assert rejected["outcome"]["status"] == "rejected" and rejected["outcome"]["reason_code"] == "active_run_exists"
        assert get(path + "/nodes", limit=1) == initial
        assert client.get(path + "/nodes", headers={"Authorization": "Bearer " + "d" * 32},
            params={"cursor": initial["next_cursor"]}).status_code == 403
        post("/v1/graph-runs/advance", graph.command("graph.advance", {"run_id": run}))
        invocations = [post("/v1/invocations/claim", graph.command("runtime.claim", {"run_id": run,
            "worker_id": graph.env.principal.actor_id, "tool": graph.entry.descriptors[0].binding.model_dump(mode="json"),
            "lease_seconds": 90}))["outcome"]["invocation"] for _ in range(2)]
        assert len({value["activation_id"] for value in invocations}) == 2
        before = get(path + "/nodes", limit=1)
        commands = []
        for index, invocation in enumerate(invocations):
            output = copy.deepcopy(graph.payload["inputs"][0]["value"]["artifact"])
            output.update(artifact_id=f"parallel-result-{index}", schema_ref=graph.entry.descriptors[0].outputs[0].schema_ref.model_dump(mode="json"))
            commands.append(graph.command("runtime.complete", {"run_id": run, "completion": {"schema_version": "1",
                "invocation_id": invocation["invocation_id"], "attempt_id": invocation["attempt_id"], "fence": invocation["fence"],
                "outcome": {"status": "succeeded", "outputs": [{"port": "result", "artifact": output}]}}}))
        with ThreadPoolExecutor(max_workers=2) as pool:
            receipts = list(pool.map(lambda command: post("/v1/invocations/complete", command), commands))
        assert len(set(peer.prepared)) == 2
        assert all(receipt["outcome"]["status"] == "accepted" for receipt in receipts)
        assert len({receipt["outcome"]["committed"]["revision"] for receipt in receipts}) == 2
        for command, receipt in zip(commands, receipts, strict=True):
            assert post("/v1/invocations/complete", command) == receipt
            assert get("/v1/commands/runtime.complete/" + command.identity.command_id) == receipt
        stale = client.get(path + "/nodes", headers=headers, params={"cursor": before["next_cursor"]})
        assert stale.status_code == 409 and stale.json()["resnapshot"]
        post("/v1/graph-runs/advance", graph.command("graph.advance", {"run_id": run}))
        final = get(path + "/nodes")
        assert final["snapshot"]["status"] == "completed"
        assert final["snapshot"]["budget"] == {"limit": 8, "spent": 2, "reserved": 0}
        cursor, revisions, ids = initial["snapshot"]["event_cursor"], [], set()
        while True:
            page = get(path + "/invalidations", cursor=cursor, limit=1)
            assert get(path + "/invalidations", cursor=cursor, limit=1) == page
            revisions.extend(item["revision"] for item in page["entries"])
            ids.update(item["event_id"] for item in page["entries"])
            cursor = page["next_cursor"]
            if not page["has_more"]:
                break
        assert revisions == list(range(initial["snapshot"]["cut"]["revision"] + 1, final["snapshot"]["cut"]["revision"] + 1))
        assert len(ids) == len(revisions)
        assert not get(path + "/invalidations", cursor=cursor)["entries"]
        for invocation in invocations:
            detail = get(path + "/nodes/" + invocation["activation_id"], snapshot_token=final["snapshot"]["snapshot_token"])
            assert len(detail["attempts"]) == 1 and detail["attempts"][0]["canonical_result"]
        # Fault injection simulates a restored owner behind a previously accepted cursor.
        with graph.env.engine.begin() as conn:
            conn.execute(text("UPDATE runtime.runs SET revision=revision-1 WHERE run_id=:run"), {"run": run})
        restored = client.get(path + "/invalidations", headers=headers, params={"cursor": cursor})
        assert restored.status_code == 409 and restored.json()["resnapshot"]
        # Restore the valid cut, then simulate a missing tail event; neither is a production API.
        with graph.env.engine.begin() as conn:
            conn.execute(text("UPDATE runtime.runs SET revision=revision+2 WHERE run_id=:run"), {"run": run})
        gap = client.get(path + "/invalidations", headers=headers, params={"cursor": cursor})
        assert gap.status_code == 409 and gap.json()["resnapshot"]
        clock[0] += 61
        expired = client.get(path + "/invalidations", headers=headers, params={"cursor": cursor})
        assert expired.status_code == 410 and expired.json()["resnapshot"]
        folder = Path(__file__).absolute().parents[4] / ".test-results/graph-observation-workflow"
        folder.mkdir(parents=True, exist_ok=True)
        evidence = {"verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
            "scope": graph.env.principal.scope.model_dump(mode="json"), "run_id": run,
            "admission": admitted, "second_campaign": rejected, "completion_receipts": receipts,
            "initial_cut": initial["snapshot"]["cut"], "final_cut": final["snapshot"]["cut"],
            "budget": final["snapshot"]["budget"], "event_revisions": revisions, "event_ids": sorted(ids),
            "parallel_prepared_intents": sorted(set(peer.prepared)), "duplicate_receipts_and_pages_unchanged": True,
            "stale_page": stale.json(), "restored_behind_cursor": restored.json(), "missing_event": gap.json(),
            "expired_cursor": expired.json(), "revoked_read_action_status": 403,
            "tier": "public ASGI handlers and PostgreSQL; scripted Artifact reservations; no installed-peer claim"}
        (folder / (graph.env.principal.scope.project_id + ".json")).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
