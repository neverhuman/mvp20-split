"""Build isolated Planning closures and prove own-state process replacement."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import URL

from build_tool_images import closure
from check_boundaries import ROOT, project_specs
from postgres_fixture import owned_state, planning_owner


def verify(output, legacy_manifest=None):
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
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", timeout=360)
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
        assert any(name.endswith("r0004_dispatch.sql") for name in archive.namelist())
        assert any(name.endswith("r0005_task_output.sql") for name in archive.namelist())
        assert any(name.endswith("r0006_extraction.sql") for name in archive.namelist())
        assert any(name.endswith("r0007_trace_publication.sql") for name in archive.namelist())
        assert any(name.endswith("r0008_repair_families.sql") for name in archive.namelist())
        assert any(name.endswith("r0009_repair_preparation.sql") for name in archive.namelist())
        assert any(name.endswith("r0010_result_publication.sql") for name in archive.namelist())
        assert any(name.endswith("result_publication/candidate-answer-v1.schema.json") for name in archive.namelist())
        assert any(name.endswith("repair/feedback-v1.schema.json") for name in archive.namelist())
        assert any(name.endswith("repair/feedback-publication-v1.schema.json") for name in archive.namelist())
        assert any(name.endswith("publication/extraction-trace-v1.schema.json") for name in archive.namelist())
        assert any(name.endswith("prompts/domain-decomposition-v1.txt") for name in archive.namelist())
        assert any(name.endswith("prompts/domain-decomposition-v2.txt") for name in archive.namelist())
        assert not any("/tests/" in name for name in archive.namelist())
    external = ["pydantic", "pydantic-core", "annotated-types", "typing-extensions", "typing-inspection",
        "sqlalchemy", "psycopg", "psycopg-binary", "alembic", "Mako", "MarkupSafe",
        "pytest", "pluggy", "packaging", "iniconfig", "colorama", "pygments",
        "jsonschema", "jsonschema-specifications", "referencing", "rpds-py", "attrs"]
    constraints = output / "constraints.txt"
    constraints.write_text("\n".join(name + "==" + version(name) for name in external) + "\n", encoding="utf-8")
    interpreters = {}
    for label in ("initial", "replacement"):
        installation = output / label
        run([uv, "venv", "--python", "3.12", installation])
        python = installation / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([uv, "pip", "install", "--python", python, "--constraint", constraints,
             *sorted(wheels.glob("*.whl")), "pytest", "jsonschema"])
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
    dispatches = {}
    for stage, label in (("dispatch_prepare", "initial"), ("dispatch_run", "replacement"),
                         ("dispatch_replay", "replacement")):
        dispatches[stage] = run([interpreters[label], "-I", output / "tests/service/acceptance/journal_probe.py",
                                stage, project], env=probe_env, capture=True)
        if stage == "dispatch_prepare":
            time.sleep(1.1)
    assert len({r["pid"] for r in dispatches.values()}) == 3
    assert dispatches["dispatch_prepare"]["status"] == "pending"
    assert dispatches["dispatch_run"]["records"] == dispatches["dispatch_replay"]["records"]
    assert dispatches["dispatch_run"]["calls"] == [2] and dispatches["dispatch_replay"]["calls"] == []
    assert dispatches["dispatch_run"]["charges"] == [40, 40]
    typed = {}
    for stage, label in (("write", "initial"), ("replay", "replacement")):
        typed[stage] = run([interpreters[label], "-I", output / "tests/service/acceptance/task_output_probe.py",
                           stage, project], env=probe_env, capture=True)
    assert typed["write"]["pid"] != typed["replay"]["pid"]
    assert {k: v for k, v in typed["write"].items() if k not in {"pid", "calls"}} == {
        k: v for k, v in typed["replay"].items() if k not in {"pid", "calls"}}
    assert typed["write"]["calls"] == [1] and typed["replay"]["calls"] == []
    extraction = {}
    for stage, label in (("failed", "initial"), ("repair", "replacement"), ("replay", "replacement")):
        extraction[stage] = run([interpreters[label], "-I", output / "tests/service/acceptance/extraction_probe.py",
                                stage, project], env=probe_env, capture=True)
    assert len({record["pid"] for record in extraction.values()}) == 3
    assert len({record["task_sha256"] for record in extraction.values()}) == 1
    assert len({record["registered_at"] for record in extraction.values()}) == 1
    assert extraction["failed"]["traces"] == extraction["repair"]["traces"][:1]
    assert extraction["repair"]["traces"] == extraction["replay"]["traces"]
    assert [row["status"] for row in extraction["replay"]["traces"]] == ["invalid", "proposed"]
    assert extraction["replay"]["charges"] == [40, 40]
    edits = {}
    for stage, label in (("failed", "initial"), ("repair", "replacement"), ("replay", "replacement")):
        edits[stage] = run([interpreters[label], "-I", output / "tests/service/acceptance/extraction_probe.py",
                           stage, project, "edits"], env=probe_env, capture=True)
    assert len({record["pid"] for record in edits.values()}) == 3
    assert all(record["task_version"] == "2" and
               record["output_profile"]["schema_id"] == "planning.extraction-edit-draft" for record in edits.values())
    assert len({record["task_sha256"] for record in edits.values()}) == 1
    assert len({record["registered_at"] for record in edits.values()}) == 1
    assert edits["failed"]["traces"] == edits["repair"]["traces"][:1]
    assert edits["repair"]["traces"] == edits["replay"]["traces"]
    assert [row["status"] for row in edits["replay"]["traces"]] == ["invalid", "proposed"]
    assert edits["replay"]["charges"] == [40, 40]
    families = {}
    for stage, label in (("prepare", "initial"), ("run", "replacement"), ("replay", "replacement")):
        families[stage] = run([interpreters[label], "-I", output / "tests/service/acceptance/repair_family_probe.py",
                              stage, project], env=probe_env, capture=True)
    assert len({record["pid"] for record in families.values()}) == 3
    for field in ("root", "child", "reservation_at", "blocked"):
        assert families["prepare"][field] == families["run"][field] == families["replay"][field]
    assert families["prepare"]["traces"] == families["run"]["traces"][:1]
    assert families["run"]["traces"] == families["replay"]["traces"]
    exposure = {}
    for stage, label in (("overage_write", "initial"), ("overage_replay", "replacement")):
        exposure[stage] = run([interpreters[label], "-I", output / "tests/service/acceptance/repair_family_probe.py",
                              stage, project], env=probe_env, capture=True)
    assert exposure["overage_write"]["pid"] != exposure["overage_replay"]["pid"]
    assert {key: value for key, value in exposure["overage_write"].items() if key not in {"pid", "calls"}} == {
        key: value for key, value in exposure["overage_replay"].items() if key not in {"pid", "calls"}}
    workflow = {}
    for stage, label in (("prepare", "initial"), ("run", "replacement"), ("replay", "replacement")):
        result_path = output / ("repair-workflow-" + stage + ".json")
        stage_env = {**probe_env, "AMPHORA_REPAIR_STAGE": stage, "AMPHORA_REPAIR_PROJECT": project,
                     "AMPHORA_REPAIR_RESULT": str(result_path)}
        run([interpreters[label], "-I", "-m", "pytest", output / "tests/service/acceptance/repair_workflow_probe.py",
             "--import-mode=importlib", "--tb=short", "-q"], env=stage_env)
        workflow[stage] = json.loads(result_path.read_text(encoding="utf-8"))
    assert len({record["pid"] for record in workflow.values()}) == 3
    for field in ("manifest", "registered_at", "request", "packet", "reservation"):
        assert len({record[field] for record in workflow.values()}) == 1
    assert workflow["run"]["trace"] == workflow["replay"]["trace"]
    assert workflow["run"]["settlement"] == workflow["replay"]["settlement"]
    results = {}
    for stage, label in (("prepare", "initial"), ("stream", "initial"), ("recover", "replacement"), ("replay", "replacement")):
        result_path = output / ("result-storage-" + stage + ".json")
        result_env = {**probe_env, "AMPHORA_RESULT_STAGE": stage, "AMPHORA_RESULT_PROJECT": project,
            "AMPHORA_RESULT_ORIGIN": str(output / "result-storage-prepare.json"), "AMPHORA_RESULT_OUTPUT": str(result_path)}
        run([interpreters[label], "-I", "-m", "pytest", output / "tests/service/acceptance/result_storage_probe.py",
             "--import-mode=importlib", "--tb=short", "-q"], env=result_env)
        results[stage] = json.loads(result_path.read_bytes())
        if stage == "stream":
            time.sleep(1.1)  # Deliberately abandoned one-second lease; no fixture reset.
    assert len({record["pid"] for record in results.values()}) == 4
    assert len({(record["identity"], record["payload"], record["prepared_at"]) for record in results.values()}) == 1
    assert results["stream"]["outcome"] == "streaming" and results["recover"]["upload_ordinal"] == 2
    assert {k: v for k, v in results["recover"].items() if k not in {"pid", "stage"}} == {
        k: v for k, v in results["replay"].items() if k not in {"pid", "stage"}}
    legacy = None
    if legacy_manifest is not None:
        legacy_path = legacy_manifest.absolute()
        previous = json.loads(legacy_path.read_text(encoding="utf-8"))
        legacy = run([interpreters["replacement"], "-I", output / "tests/service/acceptance/journal_probe.py",
                      "replay", previous["project"]], env=probe_env, capture=True)
        assert legacy["attempts"] == previous["stages"]["replay"]["attempts"]
        assert legacy["request_sha256"] == previous["stages"]["replay"]["request_sha256"]
    manifest = {"verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed", "tests": tests, "project": project, "stages": stages,
        "reservation_stages": reservations, "settlement_stages": settlements, "dispatch_stages": dispatches,
        "typed_stages": typed, "extraction_stages": extraction, "edit_stages": edits, "family_stages": families,
        "unsettled_exposure_stages": exposure, "repair_workflow_stages": workflow, "result_storage_stages": results, "legacy_replay": legacy,
        "wheels": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(wheels.glob("*.whl"))},
        "limits": ["Own PostgreSQL journal only; no live provider/domain acceptance", "Deterministic bounded dispatch only; no actual remote transport",
                   "Two independent installs from one source-built wheel closure; no new implementation rewrite"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "tests": tests, "processes": 31 + (legacy is not None), "installations": 2}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--legacy-manifest", type=Path)
    args = parser.parse_args()
    verify(args.output, args.legacy_manifest)
