"""Actual installed Data/Planning publication, abrupt recovery and current rights."""

import argparse
import json
import os
import shutil
import subprocess
import time
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
    manifest = json.loads((installation / "manifest.json").read_bytes())
    assert manifest["status"] == "passed"
    output.mkdir(parents=True, exist_ok=False)
    initial = installation / "initial/Scripts/python.exe"
    replacement = installation / "replacement/Scripts/python.exe"
    for python, package, expected in ((initial, "amphora-agent-planning", "0.15.0"),
        (replacement, "amphora-agent-planning", "0.15.0"), (data_python, "amphora-data-artifacts", "0.29.0")):
        subprocess.run([str(python), "-I", "-c", "from importlib.metadata import version; "
                        f"assert version('{package}') == '{expected}'"], check=True, timeout=30)
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="planning_service", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "COMSPEC"}}
    environment["PYTHONUTF8"] = "1"
    scope = {"tenant_id": "planning-publication-actual", "project_id": uuid.uuid4().hex}
    config, token, profile = configure(output, scope)
    data_env = dict(environment, PUBLICATION_DATA_DATABASE=url.set(username="artifact_service").render_as_string(hide_password=False),
                    PUBLICATION_DATA_TOKEN=token)
    planning_env = dict(environment, AMPHORA_TEST_PLANNING_SERVICE_URL=url.render_as_string(hide_password=False),
                        PUBLICATION_DATA_TOKEN=token)
    probe = output / "publication_probe.py"
    shutil.copyfile(PLANNING / "tests/acceptance/publication_probe.py", probe)
    owner = DataHost(data_python, config, data_env, token)
    owner_pids, workers, records = [owner.process.pid], [], {}
    try:
        fixture, rights, source, inputs = populate(owner, output, scope, profile)

        def run(label, mode, publication, python=replacement):
            evidence_path = output / (label + ".json")
            env = dict(planning_env, PUBLICATION_DATA_ENDPOINT=owner.endpoint)
            result = subprocess.run([str(python), "-I", str(probe), mode, str(fixture), publication, str(evidence_path)],
                env=env, cwd=output, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", timeout=60)
            with (output / "workers.log").open("a", encoding="utf-8") as log:
                log.write(label + "\n" + result.stdout)
            assert result.returncode == (73 if mode.startswith("crash-") else 0), f"Probe failed: {label}; inspect workers.log"
            record = json.loads(evidence_path.read_bytes())
            workers.append(record["pid"])
            if records:
                assert record["model_calls"] == []
            records[label] = record
            return record

        baseline = run("baseline", "publish", "baseline", initial)
        assert baseline["state"]["stage"] == "finalized" and baseline["model_calls"] == [1]
        expected = sorted(ref["artifact_id"] for ref in inputs)
        assert sorted(ref["artifact_id"] for ref in baseline["state"]["result"]["declaration"]["inputs"]) == expected
        for boundary in ("prepared", "streaming", "streamed", "remote-finalize"):
            interrupted = run(boundary + "-interrupted", "crash-" + boundary, boundary, initial)
            time.sleep(8.2)  # Natural expiration of the narrower probe lease, no DB edits.
            resumed = run(boundary + "-resumed", "publish", boundary)
            before, after = interrupted["state"], resumed["state"]
            assert after["stage"] == "finalized" and after["events"][:len(before["events"])] == before["events"]
            assert after["prepared_at"] == before["prepared_at"] and after["payload_sha256"] == before["payload_sha256"]
            assert after["ordinal"] == (2 if boundary == "streaming" else 1)
            if boundary == "streaming":
                assert after["upload_id"] != before["upload_id"] and after["begin_id"] != before["begin_id"]
            else:
                assert after["finalize_id"] == before["finalize_id"]
            if boundary == "remote-finalize":
                assert after["result"]["artifact"] == interrupted["remote_artifact"]

        source_route = "/v1/acquisition/sources/document/r1"
        source_before, trace_before = owner.call("GET", source_route), owner.call("GET", "/v1/acquisition/traces/conversion")
        owner.close()
        owner = DataHost(data_python, config, data_env, token)
        owner_pids.append(owner.process.pid)
        assert owner.call("GET", source_route) == source_before == source
        assert owner.call("GET", "/v1/acquisition/traces/conversion") == trace_before
        replay = run("replacement-replay", "read", "baseline")
        assert replay["state"] == baseline["state"]

        def revise(uses):
            nonlocal rights
            previous = rights["reference"]
            rights = dict(rights, reference=dict(previous, revision=previous["revision"] + 1),
                          supersedes=previous, allowed_uses=uses)
            owner.call("POST", "/v1/acquisition/rights", rights)

        for phase, boundary in (("begin", "prepared"), ("finalize", "streamed")):
            name = "rights-" + phase
            interrupted = run(name + "-prepared", "crash-" + boundary, name, initial)
            revise(["read"])
            time.sleep(8.2)
            denied = run(name + "-denied", "rights-denied", name)
            assert (denied["state"]["stage"] == "rejected" and denied["state"]["rejection"]) or (
                denied.get("access_denial") == "command_request_denied" and
                denied["state"]["stage"] == ("prepared" if phase == "begin" else "finalizing"))
            assert denied["state"]["events"][:len(interrupted["state"]["events"])] == interrupted["state"]["events"]
            # HTTP denial alone does not classify commit state. Observe the
            # owner's exact original receipt before asserting terminal behavior.
            family = "artifacts.begin_derived_upload" if phase == "begin" else "artifacts.finalize"
            key = denied["state"]["begin_id" if phase == "begin" else "finalize_id"]
            receipt = owner.call("GET", f"/v1/commands/{family}/{key}")
            assert receipt["identity"]["command_id"] == key and receipt["identity"]["scope"] == scope
            assert receipt["outcome"]["status"] == "rejected"
            (output / (name + "-owner-receipt.json")).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
            retained = run(name + "-baseline", "read", "baseline")
            assert retained["state"] == baseline["state"]
            revise(["read", "process"])
            after_grant = run(name + "-reauthorized", "publish", name)
            assert after_grant["state"]["stage"] == "rejected"
            assert after_grant["state"]["rejection"] == receipt["outcome"]["reason_code"]
            assert after_grant["state"]["begin_id"] == denied["state"]["begin_id"]
            assert after_grant["state"]["finalize_id"] == denied["state"]["finalize_id"]
            future = run(name + "-future", "publish", name + "-future")
            assert future["state"]["stage"] == "finalized"

        assert len(set(workers)) == len(workers) and len(set(owner_pids)) == 2
        evidence = {"status": "passed", "verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
            "scope": scope, "planning_version": "0.15.0", "data_version": "0.29.0", "workers": workers,
            "data_processes": owner_pids, "records": records, "inputs": inputs,
            "limits": ["Synthetic source and deterministic provider; no real model or scientific validity",
                       "Abrupt process exits, not machine power-loss durability", "No Knowledge acceptance authority"]}
        (output / "manifest.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "passed", "planning_processes": len(workers), "data_processes": len(owner_pids)}))
    finally:
        owner.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--data-python", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation, args.data_python)
