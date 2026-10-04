"""Installed repair execution with actual Data processing rights and replacement."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from planning_publication_fixture import PLANNING, DataHost, configure, populate
from postgres_fixture import owned_state
from sqlalchemy import URL


def verify(output, installation, data_python):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit retained PostgreSQL fixture opt-in required")
    output, installation, data_python = output.absolute(), installation.absolute(), data_python.absolute()
    assert json.loads((installation / "manifest.json").read_bytes())["status"] == "passed"
    output.mkdir(parents=True, exist_ok=False)
    initial, replacement = (installation / label / "Scripts/python.exe" for label in ("initial", "replacement"))
    for python, package, expected in ((initial, "amphora-agent-planning", "0.23.0"),
            (replacement, "amphora-agent-planning", "0.23.0"), (data_python, "amphora-data-artifacts", "0.29.0")):
        subprocess.run([str(python), "-I", "-c", "from importlib.metadata import version; "
                        f"assert version('{package}') == '{expected}'"], check=True, timeout=30)
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="planning_service", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "COMSPEC"}}
    environment["PYTHONUTF8"] = "1"
    scope = {"tenant_id": "planning-repair-actual", "project_id": uuid.uuid4().hex}
    config, token, profile = configure(output, scope)
    document = json.loads(config.read_bytes())
    schema = (PLANNING / "src/amphora_agent_planning/repair/feedback-publication-v1.schema.json").read_bytes()
    schema_path = output / "feedback-publication-v1.schema.json"
    schema_path.write_bytes(schema)
    document["profiles"].append({"media_type": "application/json", "schema_id": "planning.repair-feedback-publication-content",
        "version": "1", "sha256": hashlib.sha256(schema).hexdigest(), "schema_path": schema_path.name})
    config.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    data_env = dict(environment, PUBLICATION_DATA_DATABASE=url.set(username="artifact_service").render_as_string(hide_password=False),
                    PUBLICATION_DATA_TOKEN=token)
    planning_env = dict(environment, AMPHORA_TEST_PLANNING_SERVICE_URL=url.render_as_string(hide_password=False),
                        PUBLICATION_DATA_TOKEN=token)
    probe = output / "repair_data_probe.py"
    shutil.copyfile(PLANNING / "tests/acceptance/repair_data_probe.py", probe)
    owner = DataHost(data_python, config, data_env, token)
    pids, records = [owner.process.pid], {}
    try:
        fixture, rights, _, _ = populate(owner, output, scope, profile)
        refs = output / "repair-inputs.json"
        def run(label, mode, python=replacement):
            result_path = output / (label + ".json")
            result = subprocess.run([str(python), "-I", str(probe), mode, str(fixture), str(refs), str(result_path)],
                cwd=output, env=dict(planning_env, PUBLICATION_DATA_ENDPOINT=owner.endpoint),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", timeout=90)
            with (output / "workers.log").open("a", encoding="utf-8") as stream:
                stream.write(label + "\n" + result.stdout)
            assert result.returncode == 0, f"Repair Data probe failed: {label}; inspect workers.log"
            records[label] = json.loads(result_path.read_bytes())
            return records[label]
        def revise(uses):
            nonlocal rights
            previous = rights["reference"]
            rights = dict(rights, reference=dict(previous, revision=previous["revision"] + 1),
                          supersedes=previous, allowed_uses=uses)
            owner.call("POST", "/v1/acquisition/rights", rights)
        run("publish", "publish", initial)
        missing = run("missing", "missing")
        wrong = run("wrong-bytes", "wrong-bytes")
        assert not missing["calls"] and not wrong["calls"]
        assert missing["reason"] == "source_reference_unavailable" and wrong["reason"] == "source_artifact_bytes"
        prepared = run("prepared", "prepare", initial)
        revise(["read"])
        denied = run("denied-before-issuance", "denied")
        assert denied["reason"] == "source_access_denied" and not denied["calls"]
        revise(["read", "process"])
        executed = run("run", "run")
        assert len(executed["calls"]) == 1 and executed["processing_reads"]
        assert executed["manifest"] == prepared["manifest"] and executed["registered_at"] == prepared["registered_at"]
        revise(["read"])
        owner.close()
        owner = DataHost(data_python, config, data_env, token)
        pids.append(owner.process.pid)
        replay = run("replacement-replay", "replay")
        assert not replay["calls"] and not replay["processing_reads"]
        assert replay["trace"] == executed["trace"] and replay["manifest"] == prepared["manifest"]
        manifest = {"status": "passed", "verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
            "scope": scope, "data_processes": pids, "stages": records,
            "limits": ["Actual Data0.29 public publication/processing rights; Planning0.23 own SQL only",
                "Graph profile is scripted; actual Knowledge read compatibility is a separate proof",
                "Synthetic diagnostic producer and provider; no automatic production publisher or scientific validity",
                "Wrong bytes are deliberate local response tampering after an actual Data read",
                "Process replacement uses normal exits, not abrupt crash or power-loss proof"]}
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "passed", "planning_processes": len(records), "data_processes": len(pids)}))
    finally:
        owner.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--data-python", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation, args.data_python)
