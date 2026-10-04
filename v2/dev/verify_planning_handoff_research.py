"""Isolated Planning handoffs recover actual Research declarations after owner restart."""

import argparse
import json
import os
import secrets
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import URL

from planning_knowledge_fixture import ReadOwnerHost
from postgres_fixture import owned_state, planning_owner, research_owner


def verify(output, installation, research_python, research_replacement):
    assert os.environ.get("AMPHORA_TEST_POSTGRES") == "1", "Explicit retained PostgreSQL opt-in required"
    output, installation = output.absolute(), installation.absolute()
    research_python, research_replacement = research_python.absolute(), research_replacement.absolute()
    assert json.loads((installation / "manifest.json").read_bytes())["status"] == "passed"
    output.mkdir(parents=True, exist_ok=False)
    state = owned_state()
    planning_owner(state)
    research_owner(state)
    host, port = state["endpoint"].split(":")
    base = URL.create("postgresql+psycopg", username="planning_service", password=state["password"],
        host=host, port=int(port), database=state["database"])
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA"}}
    environment["PYTHONUTF8"] = "1"
    interpreters = {label: installation / label / "Scripts/python.exe" for label in ("initial", "replacement")}

    def run(python, args, env):
        result = subprocess.run([str(python), "-I", *map(str, args)], cwd=output, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", timeout=120)
        with (output / "workers.log").open("a", encoding="utf-8") as stream:
            stream.write(result.stdout)
        assert result.returncode == 0, "Handoff Research acceptance failed; inspect workers.log"

    for python in interpreters.values():
        run(python, ["-c", "from importlib.metadata import version; assert version('amphora-agent-planning') == '0.30.0'"], environment)
    for python in (research_python, research_replacement):
        run(python, ["-c", "from importlib.metadata import version; assert version('amphora-research') == '0.34.0'"], environment)
    project = uuid.uuid4().hex
    scope = {"tenant_id": "planning-owner-handoff", "project_id": project}
    token, denied = secrets.token_hex(32), secrets.token_hex(32)
    configuration = {"database_url_env": "HANDOFF_RESEARCH_DB", "declarations": True, "principals": [
        {"token_env": "HANDOFF_RESEARCH_TOKEN", "actor_id": "fixture", "scope": scope,
         "actions": ["declare_question", "declare_evidence_need", "read_declarations"]},
        {"token_env": "HANDOFF_RESEARCH_DENIED", "actor_id": "fixture", "scope": scope, "actions": ["resolve_identity"]}]}
    config = output / "research.json"
    config.write_text(json.dumps(configuration), encoding="utf-8")
    host_env = {**environment, "HANDOFF_RESEARCH_DB": base.set(username="research_service").render_as_string(hide_password=False),
        "HANDOFF_RESEARCH_TOKEN": token, "HANDOFF_RESEARCH_DENIED": denied}
    probe = installation / "tests/service/acceptance/handoff_research_probe.py"
    owner = ReadOwnerHost(research_python, config, host_env, module="amphora_research")
    pids, records = [owner.process.pid], {}
    try:
        for stage, label in (("uncertain", "initial"), ("denied", "initial"), ("recover", "replacement"),
                             ("replay", "replacement"), ("need", "replacement"), ("need-replay", "replacement")):
            if stage == "recover":
                owner.close()
                owner = ReadOwnerHost(research_replacement, config, host_env, module="amphora_research")
                pids.append(owner.process.pid)
            result_path = output / (stage + ".json")
            worker_env = {**environment, "AMPHORA_TEST_PLANNING_SERVICE_URL": base.render_as_string(hide_password=False),
                "AMPHORA_HANDOFF_STAGE": stage, "AMPHORA_HANDOFF_PROJECT": project,
                "AMPHORA_HANDOFF_ORIGIN": str(output / "uncertain.json"), "AMPHORA_HANDOFF_OUTPUT": str(result_path),
                "AMPHORA_HANDOFF_ENDPOINT": owner.endpoint,
                "AMPHORA_HANDOFF_TOKEN": denied if stage in {"denied", "replay", "need-replay"} else token}
            run(interpreters[label], ["-m", "pytest", probe, "--import-mode=importlib", "--tb=short", "-q"], worker_env)
            records[stage] = json.loads(result_path.read_bytes())
    finally:
        owner.close()
    assert len(set(pids)) == 2 and len({record["pid"] for record in records.values()}) == 6
    assert len({(records[stage]["request"], records[stage]["payload"], records[stage]["prepared_at"])
                for stage in ("uncertain", "denied", "recover", "replay")}) == 1
    assert records["recover"]["events"] == records["replay"]["events"]
    assert records["need"]["events"] == records["need-replay"]["events"]
    assert records["need"]["payload"] == records["need-replay"]["payload"]
    manifest = {"status": "passed", "verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "planning": "0.30.0", "research": "0.34.0", "project": project, "research_pids": pids, "stages": records,
        "limits": ["Actual Research HTTP and owner restart; synthetic lost reply after committed success, not abrupt process death",
            "Scripted public Data/source fixtures; no actual Data processing-rights or Knowledge acceptance claim",
            "Two isolated Planning and Research installations from their existing verified wheel closures",
            "Historical terminal replay under denied credentials performs zero owner calls; no scientific adequacy claim",
            "Planning0011/Research0013 unchanged; no fixture reset or old migrator"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "workers": 6, "research_hosts": 2}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--research-python", type=Path, required=True)
    parser.add_argument("--research-replacement", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation, args.research_python, args.research_replacement)
