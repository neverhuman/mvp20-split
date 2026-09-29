"""A killed source-graph controller resumes accepted generation work exactly once."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog, ReviewedPlan
from amphora_contracts_campaigns import parse_executable_campaign
from sqlalchemy import text

from ..bindings.support import MemoryArtifacts
from ..scheduling.test_process_recovery import CoordinatorProcess
from .catalog import STAGES, catalog
from .definition import campaign
from .test_stage_oracles import ORACLES, PINS


class SolverProcess(CoordinatorProcess):
    def __init__(self, graph, raw, documents, run, directory, name, *, interrupt=False):
        self.path = directory / (name + ".json")
        principal = graph.env.principal
        self.path.write_text(json.dumps({"principal": {"actor_id": principal.actor_id,
            "scope": principal.scope.model_dump(mode="json"), "actions": sorted(principal.actions)},
            "definition": raw, "documents": documents, "run": run, "interrupt": interrupt}), encoding="utf-8")
        env = {key: value for key, value in os.environ.items()
               if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "SYSTEMDRIVE"}}
        env.update(GRAPH_PROBE_RUNTIME_URL=graph.env.engine.url.render_as_string(hide_password=False),
                   PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        self.log = self.path.with_suffix(".log").open("w", encoding="utf-8")
        self.process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("process_probe.py")), str(self.path)],
            env=env, stdout=self.log, stderr=self.log, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

    def reply(self):
        self.wait(".reply")
        assert self.process.wait(timeout=10) == 0
        return json.loads(self.path.with_suffix(".reply").read_bytes())


def accepted(graph, run):
    with graph.env.engine.connect() as conn:
        return {row["activation_id"]: dict(row) for row in conn.execute(text(
            "SELECT * FROM runtime.accepted_completions WHERE run_id=:run"), {"run": run}).mappings()}


def test_killed_controller_resumes_after_accepted_generation_scores(graph_env, tmp_path):
    graph = graph_env
    case = next(case for case in ORACLES if case["name"] == "two_generations")
    releases, tools, schemas = catalog()
    raw = campaign(graph.env.principal.scope.model_dump(mode="json"), releases, 2)
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), tools, schemas)
    peer = MemoryArtifacts(graph.env.principal.scope)
    seed = peer.put({**case["config"], "source_pins": PINS}, STAGES["seed"][0].schema_ref("input"))
    shape = raw["body"]["inputs"][0]["value_type"]
    admission = GraphAdmission(graph.env.engine, PlanCatalog([entry]), bindings_enabled=True)
    receipt = admission.admit(graph.env.principal, graph.command("graph.admit", {"plan_sha256": entry.plan.sha256,
        "inputs": [{"port": "parameters", "value": {"kind": "artifact", "artifact": seed.model_dump(mode="json"),
            "representation": shape["representation"], "unit": shape["unit"]}}], "budget": {"limit": 100}}))
    run = receipt.outcome.committed.object_id
    original = SolverProcess(graph, raw, {key: body.decode() for key, body in peer.documents.items()}, run, tmp_path, "original", interrupt=True)
    try:
        original.wait(".paused")
        snapshot = json.loads(original.path.with_suffix(".snapshot").read_bytes())
        before = accepted(graph, run)
        assert [state["generation"] for state in snapshot["states"]] == [0]
        assert len([item for item in snapshot["trace"] if item["stage"] == "score"]) == 6
        assert not original.path.with_suffix(".reply").exists()
    finally:
        original.close()
    replacement = SolverProcess(graph, raw, snapshot["documents"], run, tmp_path, "replacement")
    try:
        result = replacement.reply()
    finally:
        replacement.close()
    assert result["page"]["status"] == "completed" and result["page"]["reserved"] == 0
    trace = snapshot["trace"] + result["trace"]
    states = snapshot["states"] + result["states"]
    assert [state["generation"] for state in states] == [0, 1, 2]
    for state, expected in zip(states, case["generations"], strict=True):
        assert [item["candidate"]["candidate_id"] for item in state["current"]] == expected["current"]
        assert [item["candidate"]["candidate_id"] for item in state["cumulative"]] == expected["cumulative"]
        scores = [item["input"]["candidate"] for item in trace if item["stage"] == "score" and item["input"]["candidate"]["generation"] == expected["generation"]]
        assert [item["candidate_id"] for item in scores] == list(reversed(expected["candidate_ids"]))
        assert [item["scoring_seed"] for item in scores] == list(reversed(expected["scoring_seeds"]))
    after = accepted(graph, run)
    assert all(after[key] == value for key, value in before.items())
    assert len(after) == len(trace) == result["page"]["spent"]
    folder = Path(__file__).absolute().parents[4] / ".test-results/solver-process" / graph.env.principal.scope.project_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "generation-resume.json").write_text(json.dumps({"verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scope": graph.env.principal.scope.model_dump(mode="json"), "run": run, "plan_sha256": entry.plan.sha256,
        "source_pins": PINS, "accepted_before": before, "accepted_after": after, "trace": trace, "states": states,
        "boundary": {"actual_process_killed": True, "fresh_process_replacement": True, "accepted_scores_before_kill": 6,
            "unchanged_prior_acceptances": True, "artifact_peer": "scripted"}}, default=str, indent=2) + "\n", encoding="utf-8")
