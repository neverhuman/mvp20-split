"""Observed admission contention and real process death before/after commit."""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_contracts_runtime import CommandReceipt
from sqlalchemy import text

from ..scheduling.test_process_recovery import CoordinatorProcess
from .test_admission import proposal, setup


class SuccessorProcess(CoordinatorProcess):
    def __init__(self, graph, service, directory, name, command, start, **options):
        self.path = directory / (name + ".json")
        principal = graph.env.principal
        entry = next(iter(service.catalog._entries.values()))
        self.path.write_text(json.dumps({"principal": {"actor_id": principal.actor_id,
            "scope": principal.scope.model_dump(mode="json"), "actions": sorted(principal.actions)},
            "definition": entry.plan.document.definition.model_dump(mode="json"),
            "command": json.loads(command.canonical_bytes), "start": str(start), **options}), encoding="utf-8")
        env = {key: value for key, value in os.environ.items()
               if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "SYSTEMDRIVE"}}
        env.update(GRAPH_PROBE_RUNTIME_URL=graph.env.engine.url.render_as_string(hide_password=False),
                   PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        self.log = self.path.with_suffix(".log").open("w", encoding="utf-8")
        self.process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("process_probe.py")), str(self.path)],
            env=env, stdout=self.log, stderr=self.log, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)


def ancestry(graph, parent):
    with graph.env.engine.connect() as conn:
        return [dict(row) for row in conn.execute(text("SELECT * FROM runtime.graph_successors WHERE parent_run_id=:parent"),
            {"parent": parent}).mappings()]


def record(graph, parent, case, receipts, boundary):
    rows = ancestry(graph, parent)
    assert len(rows) == 1
    document = {"verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "case": case,
        "scope": graph.env.principal.scope.model_dump(mode="json"), "parent": parent, "ancestry": rows,
        "receipts": [receipt.model_dump(mode="json") for receipt in receipts], "boundary": boundary,
        "tier": "actual independent owner processes and PostgreSQL; scalar fixture, no Artifact peer"}
    folder = Path(__file__).absolute().parents[4] / ".test-results/successor-process" / graph.env.principal.scope.project_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / (case + ".json")).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


@pytest.mark.parametrize("identical", [False, True])
def test_two_real_processes_serialize_successors(graph_env, tmp_path, identical):
    graph = graph_env
    service, payload, parent, _, _ = setup(graph)
    data = proposal(graph, payload, parent)
    first = graph.command("graph.admit_successor", data)
    commands = [first, first if identical else graph.command("graph.admit_successor", data)]
    start = tmp_path / "start"
    workers = [SuccessorProcess(graph, service, tmp_path, f"worker-{index}", command, start)
               for index, command in enumerate(commands)]
    try:
        backends = [json.loads(worker.wait(".ready").read_bytes())["backend"] for worker in workers]
        with graph.env.engine.begin() as conn:
            conn.execute(text("SELECT singleton FROM runtime.admission_guard WHERE singleton=true FOR UPDATE"))
            start.write_text("go", encoding="utf-8")
            deadline = time.monotonic() + 10
            while conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE pid=ANY(:ids) AND wait_event_type='Lock'"),
                {"ids": backends}).scalar_one() != 2:
                assert time.monotonic() < deadline, "Both actual successor processes must contend"
                conn.execute(text("SELECT pg_stat_clear_snapshot()"))
                time.sleep(0.01)
        replies = [worker.reply() for worker in workers]
        if identical:
            assert replies[0] == replies[1] and replies[0].outcome.status == "accepted"
        else:
            assert sorted(reply.outcome.status for reply in replies) == ["accepted", "rejected"]
            assert next(reply for reply in replies if reply.outcome.status == "rejected").outcome.reason_code == "active_run_exists"
        record(graph, parent, "race-identical" if identical else "race-distinct", replies,
               {"lock_waiters": 2, "backends": backends, "logical_children": 1})
    finally:
        for worker in workers:
            worker.close()


@pytest.mark.parametrize("boundary", ["before_commit", "after_commit"])
def test_killed_admission_replays_from_fresh_process(graph_env, tmp_path, boundary):
    graph = graph_env
    service, payload, parent, original, parent_receipt = setup(graph)
    parent_page = GraphReads(graph.env.engine).run(graph.env.principal, parent)
    command = graph.command("graph.admit_successor", proposal(graph, payload, parent))
    start = tmp_path / "start"
    start.write_text("go", encoding="utf-8")
    worker = SuccessorProcess(graph, service, tmp_path, "original", command, start, **{"hold_" + boundary: True})
    try:
        worker.wait(".before_commit" if boundary == "before_commit" else ".committed")
        before = ancestry(graph, parent)
        assert len(before) == (0 if boundary == "before_commit" else 1)
        committed = None if boundary == "before_commit" else CommandReceipt.model_validate_json(worker.path.with_suffix(".committed").read_bytes())
        assert not worker.path.with_suffix(".reply").exists()
    finally:
        worker.close()
    replacement = SuccessorProcess(graph, service, tmp_path, "replacement", command, start)
    try:
        reply = replacement.reply()
        assert reply.outcome.status == "accepted"
        if committed is not None:
            assert reply == committed and ancestry(graph, parent) == before
            assert not replacement.path.with_suffix(".before_commit").exists()
    finally:
        replacement.close()
    assert service.admit(graph.env.principal, original) == parent_receipt
    assert GraphReads(graph.env.engine).run(graph.env.principal, parent) == parent_page
    record(graph, parent, "death-" + boundary, [reply], {"real_process_killed": True, "fresh_process_replacement": True,
        "original_receipt_preserved": committed is not None, "rollback_observed": committed is None})
