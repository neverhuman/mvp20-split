"""Installed process crash/replacement proof against retained Planning-owned state."""

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

from postgres_fixture import ROOT, owned_state, planning_owner
from sqlalchemy import URL

SCENARIOS = {
    "reservation": (71, [1], ["abstained"], [1]),
    "issuance": (72, [2], ["unknown", "abstained"], [2]),
    "provider_return": (73, [1, 2], ["unknown", "abstained"], [2]),
    "observation": (74, [1], ["abstained"], []),
    "settlement": (75, [1], ["abstained"], []),
}


def verify(initial, replacement, output):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit retained PostgreSQL fixture opt-in required")
    initial, replacement, output = initial.absolute(), replacement.absolute(), output.absolute()
    assert initial.is_file() and replacement.is_file()
    state = owned_state()
    planning_owner(state)
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="planning_service", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    env = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "COMSPEC"}}
    env.update(PYTHONUTF8="1", AMPHORA_TEST_PLANNING_SERVICE_URL=url.render_as_string(hide_password=False))
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(ROOT / "services/agent_planning/tests", output / "tests",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    probe = output / "tests/acceptance/crash_probe.py"
    results = {}
    for scenario, (exit_code, expected_markers, expected_statuses, expected_recovery_calls) in SCENARIOS.items():
        project = uuid.uuid4().hex
        folder = output / scenario
        folder.mkdir()
        markers = folder / "markers"
        markers.mkdir()
        process_env = {**env, "AMPHORA_PLANNING_PROBE_MARKERS": str(markers)}
        stages = {}
        for phase, python in (("crash", initial), ("recover", replacement), ("replay", replacement)):
            command = [str(python), "-I", str(probe), phase, scenario, project]
            completed = subprocess.run(command, cwd=output, env=process_env, capture_output=True,
                                       text=True, encoding="utf-8", timeout=30)
            (folder / (phase + ".log")).write_text(completed.stdout + completed.stderr, encoding="utf-8")
            expected_code = exit_code if phase == "crash" else 0
            if completed.returncode != expected_code:
                raise RuntimeError(f"Planning recovery failed at {scenario}/{phase}; inspect {folder}")
            stages[phase] = json.loads(completed.stdout)
            if phase == "crash" and scenario in {"issuance", "provider_return"}:
                time.sleep(1.1)
        assert len({s["pid"] for s in stages.values()}) == 3
        assert len({s["request_sha256"] for s in stages.values()}) == 1
        assert stages["recover"]["statuses"] == stages["replay"]["statuses"] == expected_statuses
        assert stages["recover"]["records"] == stages["replay"]["records"]
        assert stages["recover"]["charges"] == stages["replay"]["charges"] == [40] * len(expected_statuses)
        assert stages["recover"]["calls"] == expected_recovery_calls and stages["replay"]["calls"] == []
        assert not (markers / "duplicate.flag").exists()
        call_records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(markers.glob("attempt-*.json"))]
        assert [r["ordinal"] for r in call_records] == expected_markers
        assert all(r["request_sha256"] == stages["crash"]["request_sha256"] for r in call_records)
        results[scenario] = {"exit_code": exit_code, "stages": stages, "synthetic_call_markers": call_records}
    manifest = {"verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed", "scenarios": results, "processes": 15,
        "initial_python": str(initial), "replacement_python": str(replacement),
        "limits": ["Abrupt os._exit at committed boundaries; not power-loss durability",
                   "Actual retained PostgreSQL; synthetic provider markers, not remote effects",
                   "Existing independent installations; no new wheel build in this harness"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "scenarios": len(results), "processes": 15}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initial", type=Path, required=True)
    parser.add_argument("--replacement", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify(args.initial, args.replacement, args.output)
