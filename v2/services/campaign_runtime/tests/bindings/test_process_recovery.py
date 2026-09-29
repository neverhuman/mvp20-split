"""Independent processes prove conversion serialization and restart boundaries."""

import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from amphora_campaign_runtime.coordinator.reads import GraphReads
from sqlalchemy import text

from ..scheduling.test_process_recovery import CoordinatorProcess
from .test_execution import advance, setup
from .test_recovery import intent


class BindingProcess(CoordinatorProcess):
    def __init__(self, e, bindings, peer, directory, name, barrier, **options):
        self.path = directory / (name + ".json")
        principal = e.env.principal
        entry = next(iter(bindings.catalog._entries.values()))
        self.path.write_text(json.dumps({"principal": {"actor_id": principal.actor_id,
            "scope": principal.scope.model_dump(mode="json"), "actions": sorted(principal.actions)},
            "definition": entry.plan.document.definition.model_dump(mode="json"),
            "schemas": [{"identity": asdict(schema.identity), "body": schema._body.decode()}
                        for schema in entry.schemas._entries.values()],
            "documents": {key: body.decode() for key, body in peer.documents.items()}, "start": str(barrier), **options}), encoding="utf-8")
        environment = {key: value for key, value in os.environ.items()
                       if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "SYSTEMDRIVE"}}
        environment.update(GRAPH_PROBE_RUNTIME_URL=e.env.engine.url.render_as_string(hide_password=False),
                           PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        self.log = self.path.with_suffix(".log").open("w", encoding="utf-8")
        self.process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("process_probe.py")), str(self.path)],
            env=environment, stdout=self.log, stderr=self.log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

    def reply(self):
        self.wait(".reply")
        assert self.process.wait(timeout=10) == 0
        return json.loads(self.path.with_suffix(".reply").read_bytes())


def record(e, run, case, boundary):
    row = intent(e, run)
    with e.env.engine.connect() as conn:
        closures = conn.execute(text("SELECT receipt_id,revision,document FROM runtime.binding_closures WHERE run_id=:run"),
                                {"run": run}).mappings().all()
        reserved = conn.execute(text("SELECT count(*) FROM runtime.binding_reservations WHERE intent_id=:intent"),
                                {"intent": row["intent_id"]}).scalar_one()
        assert tuple(conn.execute(text("SELECT spent,reserved FROM runtime.runs WHERE run_id=:run"), {"run": run}).one()) == (0, 0)
    assert len(closures) == 1
    if row["status"] == "committed":
        assert reserved == len(row["output_bindings"])
    folder = Path(__file__).absolute().parents[4] / ".test-results/binding-process" / e.env.principal.scope.project_id
    folder.mkdir(parents=True, exist_ok=True)
    document = {"verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "case": case, "scope": e.env.principal.scope.model_dump(mode="json"), "run_id": run,
        "intent_id": row["intent_id"], "status": row["status"], "outputs": row["outputs"],
        "closures": [dict(item) for item in closures], "reservations": reserved, "boundary": boundary,
        "artifact_peer": "scripted; installed peer proof remains V1"}
    (folder / (case + ".json")).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def test_competing_processes_wait_on_same_run_and_accept_once(graph_env, tmp_path):
    e = graph_env
    run, bindings, advancer, peer = setup(e, 2)
    advance(e, run, advancer)
    start = tmp_path / "start"
    workers = [BindingProcess(e, bindings, peer, tmp_path, name, start) for name in ("first", "second")]
    try:
        backends = [json.loads(worker.wait(".ready").read_bytes())["backend"] for worker in workers]
        with e.env.engine.begin() as conn:
            conn.execute(text("SELECT run_id FROM runtime.runs WHERE run_id=:run FOR UPDATE"), {"run": run})
            start.write_text("go", encoding="utf-8")
            deadline = time.monotonic() + 10
            while conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE pid=ANY(:ids) AND wait_event_type='Lock'"),
                               {"ids": backends}).scalar_one() != 2:
                assert time.monotonic() < deadline, "Both real owner processes must contend"
                conn.execute(text("SELECT pg_stat_clear_snapshot()"))
                time.sleep(0.01)
        assert sorted(worker.reply()["changed"] for worker in workers) == [False, True]
        row = intent(e, run)
        assert row["status"] == "committed"
        assert [item["artifact"]["sha256"] for item in row["outputs"][0]["value"]["items"]] == [
            hashlib.sha256(body).hexdigest() for body in (b'{"id":"second","value":5}', b'{"id":"first","value":2}')]
        record(e, run, "competing-processes", {"lock_waiters": 2, "backends": backends, "logical_acceptances": 1})
    finally:
        for worker in workers:
            worker.close()


@pytest.mark.parametrize("boundary", ["before_commit", "after_commit"])
def test_killed_process_replacement_preserves_original_conversion(graph_env, tmp_path, boundary):
    e = graph_env
    run, bindings, advancer, peer = setup(e, 2)
    advance(e, run, advancer)
    original = intent(e, run)
    start = tmp_path / "start"
    start.write_text("go", encoding="utf-8")
    worker = BindingProcess(e, bindings, peer, tmp_path, "original", start, **{"hold_" + boundary: True})
    try:
        worker.wait(".before_commit" if boundary == "before_commit" else ".committed")
        stopped = intent(e, run)
        assert stopped["status"] == ("prepared" if boundary == "before_commit" else "committed")
        assert not worker.path.with_suffix(".reply").exists()
    finally:
        worker.close()
    if boundary == "before_commit":
        # Observe real database lease expiry; never shorten a stored lease for this process proof.
        deadline = time.monotonic() + 35
        with e.env.engine.connect() as conn:
            while not conn.execute(text("SELECT lease_until<=clock_timestamp() FROM runtime.binding_intents WHERE intent_id=:intent"),
                                   {"intent": original["intent_id"]}).scalar_one():
                assert time.monotonic() < deadline
                time.sleep(0.05)
    replacement = BindingProcess(e, bindings, peer, tmp_path, "replacement", start)
    try:
        assert replacement.reply()["changed"] == (boundary == "before_commit")
        if boundary == "after_commit":
            assert not replacement.path.with_suffix(".reserving").exists()
    finally:
        replacement.close()
    row = intent(e, run)
    assert row["status"] == "committed" and row["intent_id"] == original["intent_id"]
    if boundary == "after_commit":
        assert row["outcome"] == stopped["outcome"] and row["outputs"] == stopped["outputs"]
    record(e, run, "death-" + boundary, {"real_process_killed": True, "original_identity": original["intent_id"],
        "database_lease_expiry_observed": boundary == "before_commit", "fresh_process_replacement": True})


@pytest.mark.parametrize("stop", ["cancel", "deadline"])
def test_stop_process_wins_while_reservation_process_is_paused(graph_env, tmp_path, stop):
    e = graph_env
    run, bindings, advancer, peer = setup(e, 1, timeout=8 if stop == "deadline" else 120)
    advance(e, run, advancer)
    start = tmp_path / "start"
    start.write_text("go", encoding="utf-8")
    worker = BindingProcess(e, bindings, peer, tmp_path, "reserver", start, hold_reserve=True)
    try:
        worker.wait(".reserving")
        page = GraphReads(e.env.engine).run(e.env.principal, run, version=3)
        options = {}
        if stop == "cancel":
            command = e.command("runtime.cancel", {"run_id": run, "expected_run_revision": page.revision, "reason_code": "process_stop"})
            options["cancel"] = json.loads(command.canonical_bytes)
        else:
            limit = time.monotonic() + 15
            with e.env.engine.connect() as conn:
                while not conn.execute(text("SELECT deadline<=clock_timestamp() FROM runtime.binding_intents WHERE run_id=:run"), {"run": run}).scalar_one():
                    assert time.monotonic() < limit
                    time.sleep(0.02)
        stopper = BindingProcess(e, bindings, peer, tmp_path, "stopper", start, **options)
        try:
            assert stopper.reply()["changed"] == (stop == "cancel")
        finally:
            stopper.close()
        stopped = intent(e, run)
        worker.path.with_suffix(".reserve_release").write_text("go", encoding="utf-8")
        worker.reply()
        row = intent(e, run)
        assert row["status"] == "aborted" and row["outcome"] == stopped["outcome"] and row["outputs"] is None
        with e.env.engine.connect() as conn:
            targets = conn.execute(text("SELECT target FROM runtime.outbox JOIN runtime.audit_events USING(event_id) WHERE run_id=:run"), {"run": run}).scalars().all()
        assert "artifact_reconcile" in targets and "artifact_confirm" not in targets
        if stop == "deadline":
            advance(e, run, advancer)
        assert GraphReads(e.env.engine).run(e.env.principal, run, version=3).status == (
            "cancelled" if stop == "cancel" else "blocked")
        record(e, run, stop + "-during-reserve", {"separate_stop_process": True, "late_response_reconciled": True})
    finally:
        worker.close()
