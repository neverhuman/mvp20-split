"""Actual competing/replaced coordinator processes over PostgreSQL, with independent frontier keys."""

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from amphora_contracts_runtime import CommandReceipt
from sqlalchemy import text

from .test_advancement import admit, advance, claim, complete, table


def evidence(graph, run, case, boundary):
    # Test-only synthetic identities; never serialize owner credentials, environments or SQL URLs.
    scope = graph.env.principal.scope
    folder = Path(__file__).absolute().parents[4] / ".test-results/graph-scheduling-process" / scope.project_id
    folder.mkdir(parents=True, exist_ok=True)
    with graph.env.engine.connect() as conn:
        row = conn.execute(text("SELECT plan_sha256,status,budget_limit,spent,reserved FROM runtime.runs WHERE run_id=:run"),
                           {"run": run}).mappings().one()
    result = {"case": case, "verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "scope": scope.model_dump(mode="json"), "run_id": run, "run": dict(row), "boundary": boundary,
        "frontier": sorted(({key: item[key] for key in ("activation_id", "node_id", "path", "status", "reason_code")}
                            for item in table(graph, run, "graph_nodes")), key=lambda item: item["activation_id"]),
        "workers": sorted(({key: item[key] for key in ("activation_id", "status", "attempt_count", "current_fence")}
                           for item in table(graph, run, "activations")), key=lambda item: item["activation_id"])}
    (folder / (case + ".json")).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


class CoordinatorProcess:
    def __init__(self, graph, directory, name, command, start, *, hold=False, probe=None):
        self.path = directory / (name + ".json")
        principal = graph.env.principal
        self.path.write_text(json.dumps({"principal": {"actor_id": principal.actor_id,
            "scope": principal.scope.model_dump(mode="json"), "actions": sorted(principal.actions)},
            "command": json.loads(command.canonical_bytes), "start": str(start), "hold_after_commit": hold}), encoding="utf-8")
        environment = {key: value for key, value in os.environ.items()
                       if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "SYSTEMDRIVE"}}
        environment.update(GRAPH_PROBE_RUNTIME_URL=graph.env.engine.url.render_as_string(hide_password=False),
                           PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        self.log = self.path.with_suffix(".log").open("w", encoding="utf-8")
        self.process = subprocess.Popen([sys.executable, str(probe or Path(__file__).with_name("process_probe.py")), str(self.path)],
            env=environment, stdout=self.log, stderr=self.log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

    def wait(self, suffix):
        deadline = time.monotonic() + 25
        marker = self.path.with_suffix(suffix)
        while not marker.exists():
            if self.process.poll() is not None or time.monotonic() >= deadline:
                raise AssertionError("Coordinator did not reach " + suffix + ": " + self.path.with_suffix(".log").read_text(encoding="utf-8")[-3000:])
            time.sleep(0.01)
        return marker

    def reply(self):
        self.wait(".reply")
        assert self.process.wait(timeout=10) == 0
        return CommandReceipt.model_validate_json(self.path.with_suffix(".reply").read_bytes())

    def close(self):
        if self.process.poll() is None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(self.process.pid), "/T", "/F"], capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW, timeout=10, check=True)
            else:
                self.process.kill()
            self.process.wait(timeout=10)
        self.log.close()


def expected_key(digest, node, occurrences=()):
    document = {"profile": "amphora-activation-address-v1", "plan_sha256": digest,
                "path": {"schema_version": "2", "node_id": node, "occurrences": list(occurrences)}}
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


@pytest.mark.parametrize("same_command", [False, True])
def test_two_real_coordinators_cannot_duplicate_ready_invocation(graph_env, tmp_path, same_command):
    graph = graph_env
    inputs = [*graph.payload["inputs"], {"port": "flag", "value": {"kind": "boolean", "value": True}}]
    run = admit(graph, 1, inputs)
    commands = [graph.command("graph.advance", {"run_id": run}) for _ in range(2)]
    if same_command:
        commands[1] = commands[0]
    start = tmp_path / "start"
    workers = [CoordinatorProcess(graph, tmp_path, str(index), command, start) for index, command in enumerate(commands)]
    try:
        backends = [json.loads(worker.wait(".ready").read_text(encoding="utf-8"))["backend"] for worker in workers]
        # Both processes enter advancement while the same actual owner run row is locked.
        with graph.env.engine.begin() as conn:
            conn.execute(text("SELECT run_id FROM runtime.runs WHERE run_id=:run FOR UPDATE"), {"run": run})
            start.write_text("go", encoding="utf-8")
            deadline = time.monotonic() + 10
            while conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE pid=ANY(:backends) "
                                    "AND wait_event_type='Lock'"), {"backends": backends}).scalar_one() != 2:
                assert time.monotonic() < deadline, "Both actual coordinator backends must contend before release"
                conn.execute(text("SELECT pg_stat_clear_snapshot()"))
                time.sleep(0.01)
        receipts = [worker.reply() for worker in workers]
        assert all(receipt.outcome.status == "accepted" for receipt in receipts)
        if same_command:
            assert receipts[0] == receipts[1]
        page = advance(graph, run)
        expected = {"choose": "succeeded", "left": "issued", "right": "skipped", "collect": "waiting", "finish": "waiting"}
        assert {row["activation_id"]: row["status"] for row in table(graph, run, "graph_nodes")} == {
            expected_key(page.plan_sha256, node): status for node, status in expected.items()}
        assert [row["activation_id"] for row in table(graph, run, "activations")] == [expected_key(page.plan_sha256, "left")]
        assert (page.spent, page.reserved) == (0, 0)
        evidence(graph, run, "race-same-command" if same_command else "race-distinct-commands",
                 {"coordinator_backends": backends, "observed_lock_waiters": 2, "duplicate_invocations": 0})
    finally:
        for worker in workers:
            worker.close()


def test_kill_after_commit_before_reply_recovers_original_receipt_and_dispatch(graph_env, tmp_path):
    graph = graph_env
    inputs = [*graph.payload["inputs"], {"port": "flag", "value": {"kind": "boolean", "value": False}}]
    run = admit(graph, 1, inputs)
    command = graph.command("graph.advance", {"run_id": run})
    start = tmp_path / "start"
    start.write_text("go", encoding="utf-8")
    first = CoordinatorProcess(graph, tmp_path, "original", command, start, hold=True)
    try:
        first.wait(".committed")
        assert not first.path.with_suffix(".reply").exists()
        with graph.env.engine.connect() as conn:
            original = conn.execute(text("SELECT receipt FROM runtime.commands WHERE tenant_id=:tenant AND project_id=:project "
                "AND command_id=:command"), {"tenant": graph.env.principal.scope.tenant_id,
                    "project": graph.env.principal.scope.project_id, "command": command.identity.command_id}).scalar_one()
            assert conn.execute(text("SELECT count(*) FROM runtime.outbox WHERE payload->>'kind'='graph_advanced' "
                "AND operation_id=:operation"), {"operation": original["outcome"]["binding"]["operation_id"]}).scalar_one() == 1
    finally:
        first.close()
    replacement = CoordinatorProcess(graph, tmp_path, "replacement", command, start)
    try:
        receipt = replacement.reply()
        assert receipt.model_dump(mode="json") == original
        assert len(table(graph, run, "activations")) == 1
        work = claim(graph, run)
        assert work.node_id == "right"
        complete(graph, run, work)
        assert advance(graph, run).status == "completed"
        evidence(graph, run, "kill-after-commit", {"original_reply_received": False, "original_receipt_recovered": True,
                 "notification_dispatched": False, "replacement_dispatch_completed": True})
    finally:
        replacement.close()


def process_advance(graph, run, directory, name):
    start = directory / (name + ".start")
    start.write_text("go", encoding="utf-8")
    worker = CoordinatorProcess(graph, directory, name, graph.command("graph.advance", {"run_id": run}), start)
    try:
        assert worker.reply().outcome.status == "accepted"
    finally:
        worker.close()
    return table(graph, run, "graph_runs")[0]["plan_sha256"]


def membership(items):
    value = {"profile": "amphora-scatter-membership-v1", "collection": {"kind": "collection", "items": items}}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def assert_frontier(graph, run, digest, expected):
    assert {row["activation_id"]: row["status"] for row in table(graph, run, "graph_nodes")} == {
        expected_key(digest, node, occurrences): status for node, occurrences, status in expected}


def test_process_recovery_zero_scatter_exact_empty_frontier(graph_env, tmp_path):
    graph = graph_env
    run = admit(graph, 2, [{"port": "items", "value": {"kind": "collection", "items": []}}])
    digest = process_advance(graph, run, tmp_path, "empty")
    assert_frontier(graph, run, digest, [("batch", (), "succeeded"), ("finish", (), "succeeded")])
    assert table(graph, run, "activations") == []
    assert table(graph, run, "graph_runs")[0]["outputs"] == [{"port": "results", "value": {"kind": "collection", "items": []}}]
    evidence(graph, run, "empty-scatter", {"actual_coordinator_process": True, "expected_nodes": 2, "expected_invocations": 0})


@pytest.mark.parametrize("threshold,iterations,stop", [(1, 1, "predicate"), (2, 2, "limit")])
def test_process_loop_feedback_is_committed_before_next_iteration(graph_env, tmp_path, threshold, iterations, stop):
    graph = graph_env

    def change(raw):
        loop = raw["body"]["nodes"][0]
        loop["body"]["nodes"][0]["outputs"][0]["source"] = {"kind": "integer", "value": 1, "unit": "1"}
        loop["until"]["right"]["value"] = threshold

    run = admit(graph, 3, [], modify=change)
    digest = process_advance(graph, run, tmp_path, "loop")
    expected = [("loop", (), "succeeded"), ("finish", (), "succeeded")]
    expected.extend(("finish", ({"kind": "loop", "node_id": "loop", "index": index},), "succeeded") for index in range(iterations))
    assert_frontier(graph, run, digest, expected)
    loop = next(row for row in table(graph, run, "graph_nodes") if row["node_id"] == "loop")
    assert loop["state"] == {"iteration": iterations - 1, "stop": stop}
    children = sorted((row for row in table(graph, run, "graph_scopes") if row["occurrences"]),
                      key=lambda row: row["occurrences"][0]["index"])
    assert children[0]["inputs"][0]["value"]["value"] == 0
    assert all(row["outputs"][0]["value"]["value"] == 1 for row in children)
    if iterations == 2:
        assert children[1]["inputs"] == children[0]["outputs"]
    evidence(graph, run, "loop-" + stop, {"actual_coordinator_process": True, "iterations": iterations,
             "initial_value": 0, "committed_body_value": 1, "feedback_verified": iterations == 2})


@pytest.mark.parametrize("budget", [1, 8])
def test_process_budget_block_or_independent_progress_has_exact_frontier(graph_env, tmp_path, budget):
    graph = graph_env
    items = [graph.payload["inputs"][0]["value"]] * 3
    run = admit(graph, 2, [{"port": "items", "value": {"kind": "collection", "items": items}}], budget=budget)
    digest = process_advance(graph, run, tmp_path, "initial")
    first = claim(graph, run)
    expected = []
    if budget == 1:
        complete(graph, run, first)
        process_advance(graph, run, tmp_path, "spent")
        # A later unissued member is still materialized within the bounded body, then settled without a charge.
        process_advance(graph, run, tmp_path, "exhausted")
        expected.extend([("batch", (), "blocked"), ("finish", (), "blocked")])
        for index in range(3):
            occurrence = ({"kind": "scatter", "node_id": "batch", "index": index, "membership_sha256": membership(items)},)
            expected.extend([("map", occurrence, "succeeded" if index == 0 else "failed"),
                             ("finish", occurrence, "succeeded" if index == 0 else "blocked")])
        with graph.env.engine.connect() as conn:
            assert conn.execute(text("SELECT status,spent,reserved FROM runtime.runs WHERE run_id=:run"),
                                {"run": run}).one() == ("blocked", 1, 0)
    else:
        second = claim(graph, run)
        complete(graph, run, second)
        process_advance(graph, run, tmp_path, "independent")
        expected.extend([("batch", (), "issued"), ("finish", (), "waiting")])
        for index in range(3):
            occurrence = ({"kind": "scatter", "node_id": "batch", "index": index, "membership_sha256": membership(items)},)
            expected.extend([("map", occurrence, "succeeded" if index == 1 else "issued"),
                             ("finish", occurrence, "succeeded" if index == 1 else "waiting")])
        third = claim(graph, run)
        assert third.invocation_id not in {first.invocation_id, second.invocation_id}
    assert_frontier(graph, run, digest, expected)
    evidence(graph, run, "budget-exhausted" if budget == 1 else "independent-progress", {
        "actual_coordinator_processes": 3 if budget == 1 else 2, "membership_sha256": membership(items),
        "expected_nodes": 8, "slow_branch_still_leased": budget != 1, "scripted_reservation_peer": True})
