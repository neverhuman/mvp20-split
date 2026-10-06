"""Actual process death and replay for combined draft/successor transaction."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_campaign_runtime.successors.reads import SuccessorReads
from amphora_contracts_runtime import CommandReceipt
from sqlalchemy import text

from ..scheduling.test_process_recovery import CoordinatorProcess
from .test_commands import bindings
from .test_draft_successor import next_command, prepare


class DraftProcess(CoordinatorProcess):
    def __init__(self, e, directory, name, command, start, boundary=None):
        self.path = directory / (name + ".json")
        principal = e.principal
        self.path.write_text(json.dumps({"principal": {"actor_id": principal.actor_id,
            "scope": principal.scope.model_dump(mode="json"), "actions": sorted(principal.actions)},
            "command": json.loads(command.canonical_bytes), "start": str(start), "boundary": boundary}), encoding="utf-8")
        env = {key: value for key, value in os.environ.items()
               if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "SYSTEMDRIVE"}}
        env.update(GRAPH_PROBE_RUNTIME_URL=e.engine.url.render_as_string(hide_password=False), PYTHONUTF8="1", PYTHONUNBUFFERED="1")
        self.log = self.path.with_suffix(".log").open("w", encoding="utf-8")
        self.process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("draft_successor_process.py")), str(self.path)],
            env=env, stdout=self.log, stderr=self.log, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)


def counts(e):
    with e.engine.connect() as conn:
        return {table: conn.execute(text(f"SELECT count(*) FROM runtime.{table} WHERE tenant_id=:tenant AND project_id=:project"),
                bindings(e)).scalar_one() for table in ("runs", "definition_admissions", "graph_successors")}


@pytest.mark.parametrize("boundary", ["before_commit", "after_commit"])
def test_killed_combined_admission_recovers_both_records(fixture_env, tmp_path, boundary):
    e = fixture_env
    _, service, payload, parent = prepare(e)
    parent_view = GraphReads(e.engine).run(e.principal, parent, version=3)
    command = next_command(e, payload)
    start = tmp_path / "start"
    start.write_text("go", encoding="utf-8")
    worker = DraftProcess(e, tmp_path, "original", command, start, boundary)
    expected = {"runs": 2, "definition_admissions": 2, "graph_successors": 1}
    committed = None
    try:
        worker.wait(".before_commit" if boundary == "before_commit" else ".committed")
        assert not worker.path.with_suffix(".reply").exists()
        assert counts(e) == (expected if boundary == "after_commit" else {"runs": 1, "definition_admissions": 1, "graph_successors": 0})
        if boundary == "after_commit":
            committed = CommandReceipt.model_validate_json(worker.path.with_suffix(".committed").read_bytes())
    finally:
        worker.close()
    replacement = DraftProcess(e, tmp_path, "replacement", command, start)
    try:
        receipt = replacement.reply()
        assert receipt.outcome.status == "accepted"
        if committed is not None:
            assert receipt == committed and not replacement.path.with_suffix(".before_commit").exists()
    finally:
        replacement.close()
    assert counts(e) == expected
    assert service.admit_draft_successor(e.principal, command) == receipt
    assert GraphReads(e.engine).run(e.principal, parent, version=3) == parent_view
    lineage = SuccessorReads(e.engine).lineage(e.principal, receipt.outcome.committed.object_id)
    assert lineage.carried[0].expected_value_sha256 == payload["carried"][0]["expected_value_sha256"]
    output = Path(__file__).absolute().parents[4] / ".test-results/draft-successor-process" / e.principal.scope.project_id
    output.mkdir(parents=True, exist_ok=False)
    (output / "evidence.json").write_text(json.dumps({"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "boundary": boundary, "real_process_killed": True, "fresh_process_replay": True, "counts": expected,
        "receipt": receipt.model_dump(mode="json"), "lineage": lineage.model_dump(mode="json"),
        "limit": "Actual Runtime owner/PostgreSQL, scalar fixture; no peer/network claim"}, indent=2) + "\n", encoding="utf-8")
