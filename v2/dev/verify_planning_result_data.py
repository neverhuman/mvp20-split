"""Installed diagnostic/result publication with actual Data processing rights and replacement."""

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

from sqlalchemy import URL

from planning_publication_fixture import PLANNING, DataHost, configure, populate
from postgres_fixture import owned_state


def verify(output, installation, data_python):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit retained PostgreSQL fixture opt-in required")
    output, installation, data_python = output.absolute(), installation.absolute(), data_python.absolute()
    assert json.loads((installation / "manifest.json").read_bytes())["status"] == "passed"
    output.mkdir(parents=True, exist_ok=False)
    initial, replacement = (installation / label / "Scripts/python.exe" for label in ("initial", "replacement"))
    for python, package, expected in ((initial, "amphora-agent-planning", "0.27.0"),
            (replacement, "amphora-agent-planning", "0.27.0"), (data_python, "amphora-data-artifacts", "0.29.0")):
        subprocess.run([str(python), "-I", "-c", "from importlib.metadata import version; "
                        f"assert version('{package}') == '{expected}'"], check=True, timeout=30)
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="planning_service", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "COMSPEC"}}
    environment["PYTHONUTF8"] = "1"
    scope = {"tenant_id": "planning-result-actual", "project_id": uuid.uuid4().hex}
    config, token, profile = configure(output, scope)
    document = json.loads(config.read_bytes())
    for relative, identifier in (("repair/feedback-publication-v1.schema.json", "planning.repair-feedback-publication-content"),
            ("result_publication/candidate-answer-v1.schema.json", "planning.candidate-answer-content")):
        schema = (PLANNING / "src/amphora_agent_planning" / relative).read_bytes()
        schema_path = output / Path(relative).name
        schema_path.write_bytes(schema)
        document["profiles"].append({"media_type": "application/json", "schema_id": identifier,
            "version": "1", "sha256": hashlib.sha256(schema).hexdigest(), "schema_path": schema_path.name})
    config.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    data_env = dict(environment, PUBLICATION_DATA_DATABASE=url.set(username="artifact_service").render_as_string(hide_password=False),
                    PUBLICATION_DATA_TOKEN=token)
    planning_env = dict(environment, AMPHORA_TEST_PLANNING_SERVICE_URL=url.render_as_string(hide_password=False),
                        PUBLICATION_DATA_TOKEN=token)
    probe = output / "result_data_probe.py"
    shutil.copyfile(PLANNING / "tests/acceptance/result_data_probe.py", probe)
    owner = DataHost(data_python, config, data_env, token)
    pids, records = [owner.process.pid], {}
    try:
        fixture, rights, _, _ = populate(owner, output, scope, profile)
        refs = output / "result-inputs.json"
        def run(label, mode, python=replacement):
            result_path = output / (label + ".json")
            result = subprocess.run([str(python), "-I", str(probe), mode, str(fixture), str(refs), str(result_path)],
                cwd=output, env=dict(planning_env, PUBLICATION_DATA_ENDPOINT=owner.endpoint),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", timeout=90)
            with (output / "workers.log").open("a", encoding="utf-8") as stream:
                stream.write(label + "\n" + result.stdout)
            assert result.returncode == 0, f"Result Data probe failed: {label}; inspect workers.log"
            records[label] = json.loads(result_path.read_bytes())
            return records[label]
        def revise(uses):
            nonlocal rights
            previous = rights["reference"]
            rights = dict(rights, reference=dict(previous, revision=previous["revision"] + 1),
                          supersedes=previous, allowed_uses=uses)
            owner.call("POST", "/v1/acquisition/rights", rights)
        run("seed", "seed", initial)
        revise(["read"])
        denied = run("denied", "denied")
        assert denied["reason"] == "source_access_denied" and not denied["exchanges"]
        revise(["read", "process"])
        lost = run("lost-put", "lost-put", initial)
        assert lost["reason"] == "diagnostic_publication_uncertain"
        old_puts = [path for method, path in lost["exchanges"] if method == "PUT"]
        assert len(old_puts) == 1
        owner.close()
        owner = DataHost(data_python, config, data_env, token)
        pids.append(owner.process.pid)
        recovered = run("recover", "recover")
        new_puts = [path for method, path in recovered["exchanges"] if method == "PUT"]
        assert len(new_puts) == 1 and old_puts != new_puts and not recovered["processing_reads"]
        revise(["read"])
        replay = run("replay", "replay")
        assert replay["published"] == recovered["published"] and not replay["processing_reads"] and not replay["exchanges"]
        revise(["read", "process"])
        chain = run("chain", "chain")
        assert len(chain["calls"]) == 1 and chain["steps"] == 2
        answer = run("answer", "answer")
        assert answer["answer"]["authority"] == "proposal_only"
        manifest = {"status": "passed", "verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
            "scope": scope, "data_processes": pids, "stages": records,
            "limits": ["Actual Data0.29 public publication/processing rights; Planning0.27 own SQL only",
                "Graph profile is scripted; actual Knowledge read compatibility is a separate proof",
                "Production diagnostic policy/producer; synthetic provider and graph profile, no scientific validity",
                "Uncertain PUT is a deliberate lost reply after actual Data committed the stream",
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
