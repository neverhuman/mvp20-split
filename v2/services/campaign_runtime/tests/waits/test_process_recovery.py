"""Real owner processes, measured PostgreSQL contention and exact immutable closure oracles."""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from amphora_campaign_runtime.coordinator import GraphReads
from sqlalchemy import text

from ..scheduling.test_process_recovery import CoordinatorProcess
from .test_execution import advance, observation, start, submit_command


class WaitProcess(CoordinatorProcess):
    def __init__(self, f, directory, name, command, barrier, *, issuer=False, **options):
        self.path = directory / (name + ".json")
        principal = f.issuer if issuer else f.graph.env.principal
        self.path.write_text(json.dumps({"principal": {"actor_id": principal.actor_id,
            "scope": principal.scope.model_dump(mode="json"), "actions": sorted(principal.actions)},
            "command": json.loads(command.canonical_bytes), "start": str(barrier), **options}), encoding="utf-8")
        environment = {key: value for key, value in os.environ.items()
                       if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "SYSTEMDRIVE"}}
        environment.update(GRAPH_PROBE_RUNTIME_URL=f.graph.env.engine.url.render_as_string(hide_password=False),
                           PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        self.log = self.path.with_suffix(".log").open("w", encoding="utf-8")
        self.process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("process_probe.py")), str(self.path)],
            env=environment, stdout=self.log, stderr=self.log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)


def record(f, case, boundary):
    with f.graph.env.engine.connect() as conn:
        closures = conn.execute(text("SELECT document FROM runtime.graph_wait_closures WHERE run_id=:run"),
                                {"run": f.run}).scalars().all()
        intents = conn.execute(text("SELECT intent_id,status FROM runtime.wait_retention_intents WHERE run_id=:run"),
                               {"run": f.run}).mappings().all()
    assert len(closures) == 1
    page = GraphReads(f.graph.env.engine).run(f.graph.env.principal, f.run, version=2)
    assert (page.spent, page.reserved) == (0, 0)
    folder = Path(__file__).absolute().parents[4] / ".test-results/wait-process" / f.issuer.scope.project_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / (case + ".json")).write_text(json.dumps({"case": case,
        "verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "scope": f.issuer.scope.model_dump(mode="json"), "run_id": f.run,
        "expectation_sha256": f.observation.expectation_sha256, "closures": closures,
        "intents": [dict(row) for row in intents], "boundary": boundary,
        "artifact_peer": "scripted; installed real peer acceptance remains V1"}, indent=2) + "\n", encoding="utf-8")


@pytest.mark.parametrize("expired", [False, True])
def test_receipt_and_coordinator_contend_on_owner_lock(graph_env, tmp_path, expired):
    f = start(graph_env, timeout=3 if expired else 60)
    barrier = tmp_path / "start"
    receipt_command = submit_command(f)
    workers = [WaitProcess(f, tmp_path, "receipt", receipt_command, barrier, issuer=True),
               WaitProcess(f, tmp_path, "timeout", graph_env.command("graph.advance", {"run_id": f.run}), barrier)]
    try:
        backends = [json.loads(w.wait(".ready").read_bytes())["backend"] for w in workers]
        with graph_env.env.engine.begin() as conn:
            conn.execute(text("SELECT run_id FROM runtime.runs WHERE run_id=:run FOR UPDATE"), {"run": f.run})
            barrier.write_text("go", encoding="utf-8")
            until = time.monotonic() + 10
            while conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE pid=ANY(:ids) "
                                    "AND wait_event_type='Lock'"), {"ids": backends}).scalar_one() != 2:
                assert time.monotonic() < until, "Both owner processes must actually contend"
                conn.execute(text("SELECT pg_stat_clear_snapshot()"))
                time.sleep(0.01)
            if expired:
                deadline = f.observation.expectation.deadline_us
                while conn.execute(text("SELECT extract(epoch FROM clock_timestamp())*1000000")).scalar_one() < deadline:
                    time.sleep(0.02)
        replies = [w.reply() for w in workers]
        if GraphReads(graph_env.env.engine).run(graph_env.env.principal, f.run, version=2).status == "running":
            advance(f)
        closed = observation(f).closure
        assert closed.outcome.status == ("blocked" if expired else "accepted")
        assert replies[0].outcome.status == ("rejected" if expired else "accepted")
        replacement = WaitProcess(f, tmp_path, "replay", receipt_command, barrier, issuer=True)
        try:
            assert replacement.reply() == replies[0]
        finally:
            replacement.close()
        assert observation(f).closure == closed
        record(f, "expired-race" if expired else "eligible-race", {"backends": backends, "lock_waiters": 2,
            "original_receipt_replayed": True, "deadline_elapsed_before_unlock": expired})
    finally:
        for worker in workers:
            worker.close()


@pytest.mark.parametrize("stop", ["cancel", "timeout"])
def test_stop_process_wins_during_other_process_reservation(graph_env, tmp_path, stop):
    f = start(graph_env, timeout=5 if stop == "timeout" else 60)
    barrier = tmp_path / "start"
    barrier.write_text("go", encoding="utf-8")
    command = submit_command(f)
    sender = WaitProcess(f, tmp_path, "sender", command, barrier, issuer=True, hold_reserve=True)
    try:
        sender.wait(".reserving")
        page = GraphReads(graph_env.env.engine).run(graph_env.env.principal, f.run, version=2)
        if stop == "timeout":
            with graph_env.env.engine.connect() as conn:
                while conn.execute(text("SELECT extract(epoch FROM clock_timestamp())*1000000")).scalar_one() < f.observation.expectation.deadline_us:
                    time.sleep(0.02)
            cancellation = graph_env.command("graph.advance", {"run_id": f.run})
        else:
            cancellation = graph_env.command("runtime.cancel", {"run_id": f.run,
                "expected_run_revision": page.revision, "reason_code": "process_stop"})
        canceller = WaitProcess(f, tmp_path, "canceller", cancellation, barrier)
        try:
            assert canceller.reply().outcome.status == "accepted"
        finally:
            canceller.close()
        closed = observation(f).closure
        assert closed.outcome.status == ("cancelled" if stop == "cancel" else "blocked")
        sender.path.with_suffix(".reserve_release").write_text("go", encoding="utf-8")
        assert sender.reply().outcome.status == "rejected"
        assert observation(f).closure == closed
        with graph_env.env.engine.connect() as conn:
            assert conn.execute(text("SELECT status FROM runtime.wait_retention_intents WHERE run_id=:run"),
                                {"run": f.run}).scalar_one() == "aborted"
            targets = conn.execute(text("SELECT o.target FROM runtime.outbox o JOIN runtime.audit_events a USING(event_id) "
                "WHERE a.run_id=:run"), {"run": f.run}).scalars().all()
            assert "artifact_reconcile" in targets and "artifact_confirm" not in targets
        record(f, stop + "-during-reserve", {"late_reservation_aborted": True, "closure_unchanged": True})
    finally:
        sender.close()


def test_killed_receipt_process_replays_committed_closure_without_reserving_again(graph_env, tmp_path):
    f = start(graph_env)
    barrier = tmp_path / "start"
    barrier.write_text("go", encoding="utf-8")
    command = submit_command(f)
    sender = WaitProcess(f, tmp_path, "original", command, barrier, issuer=True, hold_after_commit=True)
    try:
        sender.wait(".committed")
        assert not sender.path.with_suffix(".reply").exists()
        closed = observation(f).closure
        assert closed.outcome.status == "accepted"
        with graph_env.env.engine.connect() as conn:
            original = conn.execute(text("SELECT receipt FROM runtime.commands WHERE command_id=:id"),
                                    {"id": command.identity.command_id}).scalar_one()
    finally:
        sender.close()
    replacement = WaitProcess(f, tmp_path, "replacement", command, barrier, issuer=True)
    try:
        assert replacement.reply().model_dump(mode="json") == original
        assert not replacement.path.with_suffix(".reserving").exists()
        assert observation(f).closure == closed and advance(f).status == "completed"
        record(f, "kill-after-commit", {"original_reply_received": False, "original_receipt_replayed": True,
            "replacement_reserved_again": False})
    finally:
        replacement.close()


def test_two_prepared_receipt_processes_commit_one_closure(graph_env, tmp_path):
    f = start(graph_env)
    barrier = tmp_path / "start"
    barrier.write_text("go", encoding="utf-8")
    commands = [submit_command(f), submit_command(f)]
    workers = [WaitProcess(f, tmp_path, str(i), command, barrier, issuer=True, hold_reserve=True)
               for i, command in enumerate(commands)]
    try:
        for worker in workers:
            worker.wait(".reserving")
        for worker in workers:
            worker.path.with_suffix(".reserve_release").write_text("go", encoding="utf-8")
        replies = [worker.reply() for worker in workers]
        assert sorted(reply.outcome.status for reply in replies) == ["accepted", "rejected"]
        winner = next(command for command, reply in zip(commands, replies, strict=True) if reply.outcome.status == "accepted")
        assert observation(f).closure.outcome.receipt.receipt_id == json.loads(winner.canonical_bytes)["payload"]["receipt"]["receipt_id"]
        with graph_env.env.engine.connect() as conn:
            assert conn.execute(text("SELECT status FROM runtime.wait_retention_intents WHERE run_id=:run ORDER BY status"),
                                {"run": f.run}).scalars().all() == ["aborted", "committed"]
        record(f, "two-prepared-receipts", {"prepared_processes": 2, "accepted": 1, "rejected": 1})
    finally:
        for worker in workers:
            worker.close()
