"""Build isolated Planning closures and prove own-state process replacement."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

from build_tool_images import closure
from check_boundaries import ROOT, project_specs
from postgres_fixture import owned_state, planning_owner
from sqlalchemy import URL


def verify(output):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit retained PostgreSQL fixture opt-in required")
    state = owned_state()
    planning_owner(state)
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    log = output / "build.log"
    wheels = output / "wheels"
    wheels.mkdir()
    uv = ROOT / (".venv/Scripts/uv.exe" if os.name == "nt" else ".venv/bin/uv")
    specs = {cfg["project"]["name"]: (path, cfg, module) for path, cfg, module in project_specs()}
    # Credentials are scoped to Planning; never pass admin or peer-owner URLs to the installation.
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="planning_service", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "COMSPEC"}}
    environment.update(PYTHONUTF8="1", AMPHORA_TEST_POSTGRES="1",
        AMPHORA_TEST_PLANNING_SERVICE_URL=url.render_as_string(hide_password=False),
        AMPHORA_TEST_PLANNING_MIGRATOR_URL=url.set(username="planning_migrator").render_as_string(hide_password=False))

    def run(args, *, env=None, capture=False):
        result = subprocess.run([str(arg) for arg in args], cwd=output, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", timeout=240)
        with log.open("a", encoding="utf-8") as stream:
            stream.write(result.stdout)
        if result.returncode:
            raise RuntimeError(f"Planning independent acceptance failed; inspect {log}")
        return json.loads(result.stdout) if capture else None

    for name in sorted(closure("amphora-agent-planning", specs)):
        run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels])
    with zipfile.ZipFile(next(wheels.glob("amphora_agent_planning-*.whl"))) as archive:
        assert any(name.endswith("r0001_initial.sql") for name in archive.namelist())
        assert any(name.endswith("r0002_reservations.sql") for name in archive.namelist())
        assert any(name.endswith("r0003_settlements.sql") for name in archive.namelist())
        assert not any("/tests/" in name for name in archive.namelist())
    external = ["pydantic", "pydantic-core", "annotated-types", "typing-extensions", "typing-inspection",
        "sqlalchemy", "psycopg", "psycopg-binary", "alembic", "Mako", "MarkupSafe",
        "pytest", "pluggy", "packaging", "iniconfig", "colorama", "pygments"]
    constraints = output / "constraints.txt"
    constraints.write_text("\n".join(name + "==" + version(name) for name in external) + "\n", encoding="utf-8")
    interpreters = {}
    for label in ("initial", "replacement"):
        installation = output / label
        run([uv, "venv", "--python", "3.12", installation])
        python = installation / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([uv, "pip", "install", "--python", python, "--constraint", constraints,
             *sorted(wheels.glob("*.whl")), "pytest"])
        run([python, "-I", "-c", "import importlib.util,sys; from pathlib import Path; import amphora_agent_planning; "
            "assert Path(amphora_agent_planning.__file__).absolute().is_relative_to(Path(sys.prefix).absolute()); "
            "assert all(importlib.util.find_spec(n) is None for n in "
            "('amphora_campaign_runtime','amphora_research','amphora_knowledge','amphora_data_artifacts','fastapi'))"])
        interpreters[label] = python
    shutil.copytree(ROOT / "contracts/planning/tests", output / "tests/contracts",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(ROOT / "services/agent_planning/tests", output / "tests/service",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # Explicit CLI migration; normal owner imports do not apply DDL.
    migration_env = {**environment, "AMPHORA_PLANNING_MIGRATION_URL": environment["AMPHORA_TEST_PLANNING_MIGRATOR_URL"]}
    run([interpreters["initial"], "-I", "-m", "amphora_agent_planning.persistence.migrate"], env=migration_env)
    run([interpreters["initial"], "-I", "-m", "pytest", output / "tests", "--import-mode=importlib",
         "--tb=short", "-q", "-o", "markers=postgres: explicit retained PostgreSQL fixture", "--junitxml=" + str(output / "tests.xml")], env=environment)
    suites = ET.parse(output / "tests.xml").getroot().findall("testsuite")
    tests = sum(int(suite.attrib["tests"]) for suite in suites)
    assert tests > 0 and all(int(suite.attrib[k]) == 0 for suite in suites for k in ("errors", "failures", "skipped"))
    project = uuid.uuid4().hex
    stages = {}
    probe_env = dict(environment)
    probe_env.pop("AMPHORA_TEST_PLANNING_MIGRATOR_URL")
    for stage in ("prepare", "interrupted", "finish", "replay"):
        python = interpreters["initial" if stage in {"prepare", "interrupted"} else "replacement"]
        stages[stage] = run([python, "-I", output / "tests/service/acceptance/journal_probe.py", stage, project],
                            env=probe_env, capture=True)
    assert len({record["pid"] for record in stages.values()}) == 4
    assert len({record["request_sha256"] for record in stages.values()}) == 1
    assert stages["prepare"]["attempts"] == [{"ordinal": 1, "status": "pending"}, None]
    assert stages["interrupted"]["attempts"][0]["status"] == "unknown"
    assert stages["interrupted"]["attempts"][0]["usage"]["certainty"] == "unknown"
    assert stages["interrupted"]["attempts"][1] == {"ordinal": 2, "status": "pending"}
    assert stages["finish"]["attempts"][0] == stages["interrupted"]["attempts"][0]
    assert stages["finish"]["attempts"][1]["status"] == "proposed"
    assert stages["finish"]["attempts"] == stages["replay"]["attempts"]
    reservations = {}
    for stage, label in (("budget_prepare", "initial"), ("budget_replay", "replacement")):
        reservations[stage] = run([interpreters[label], "-I", output / "tests/service/acceptance/journal_probe.py",
                                  stage, project], env=probe_env, capture=True)
    assert reservations["budget_prepare"]["pid"] != reservations["budget_replay"]["pid"]
    assert {k: v for k, v in reservations["budget_prepare"].items() if k != "pid"} == {
        k: v for k, v in reservations["budget_replay"].items() if k != "pid"}
    assert reservations["budget_replay"]["tokens"] == 2048 and reservations["budget_replay"]["units"] == 60
    settlements = {}
    for stage, label in (("budget_settle", "initial"), ("budget_settle_replay", "replacement")):
        settlements[stage] = run([interpreters[label], "-I", output / "tests/service/acceptance/journal_probe.py",
                                  stage, project], env=probe_env, capture=True)
    assert settlements["budget_settle"]["pid"] != settlements["budget_settle_replay"]["pid"]
    assert {k: v for k, v in settlements["budget_settle"].items() if k != "pid"} == {
        k: v for k, v in settlements["budget_settle_replay"].items() if k != "pid"}
    assert settlements["budget_settle_replay"]["tokens"] == 2048
    assert settlements["budget_settle_replay"]["units"] == 60
    assert settlements["budget_settle_replay"]["overage"] is False
    manifest = {"verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed", "tests": tests, "project": project, "stages": stages,
        "reservation_stages": reservations, "settlement_stages": settlements,
        "wheels": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(wheels.glob("*.whl"))},
        "limits": ["Own PostgreSQL journal only; no live provider/domain acceptance", "No durable budget dispatch yet",
                   "Two independent installs from one source-built wheel closure; no new implementation rewrite"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "tests": tests, "processes": 8, "installations": 2}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args().output)
