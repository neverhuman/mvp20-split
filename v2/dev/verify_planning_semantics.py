"""Run test-owned synthetic semantic review on both verified Planning installations."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).absolute().parents[1]


def verify(output, installation):
    output, installation = output.absolute(), installation.absolute()
    assert json.loads((installation / "manifest.json").read_bytes())["status"] == "passed"
    output.mkdir(parents=True, exist_ok=False)
    tests = output / "tests"
    shutil.copytree(ROOT / "services/agent_planning/tests", tests, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA"}}
    environment["PYTHONUTF8"] = "1"

    def run(python, args, env=environment):
        result = subprocess.run([str(python), "-I", *map(str, args)], cwd=output, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", timeout=90)
        with (output / "workers.log").open("a", encoding="utf-8") as stream:
            stream.write(result.stdout)
        assert result.returncode == 0, "Semantic verification failed; inspect workers.log"

    reports, totals = {}, {}
    for label in ("initial", "replacement"):
        python = installation / label / "Scripts/python.exe"
        run(python, ["-c", "import pathlib,sys,amphora_agent_planning as owner; from importlib.metadata import version; "
            "assert version('amphora-agent-planning') == '0.30.0'; "
            "assert pathlib.Path(owner.__file__).absolute().is_relative_to(pathlib.Path(sys.prefix).absolute())"])
        report_path, xml = output / (label + ".json"), output / (label + ".xml")
        run(python, ["-m", "pytest", tests / "extraction/test_semantic_review.py", tests / "extraction/test_corpus.py",
            tests / "acceptance/semantic_report_probe.py", "--import-mode=importlib", "--tb=short", "-q", "--junitxml", xml],
            {**environment, "AMPHORA_SEMANTIC_REPORT": str(report_path)})
        suites = list(ET.parse(xml).getroot().iter("testsuite"))
        total = {key: sum(int(row.get(key, 0)) for row in suites) for key in ("tests", "errors", "failures", "skipped")}
        assert total["tests"] > 0 and total["errors"] == total["failures"] == total["skipped"] == 0
        totals[label] = {**total, "seconds": sum(float(row.get("time", 0)) for row in suites)}
        reports[label] = json.loads(report_path.read_bytes())
    assert reports["initial"]["pid"] != reports["replacement"]["pid"]
    assert {key: value for key, value in reports["initial"].items() if key != "pid"} == {
        key: value for key, value in reports["replacement"].items() if key != "pid"}
    manifest = {"status": "passed", "verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "planning": "0.30.0", "tests": totals, "processes": 2, "reports": {
            label: {"file": label + ".json", "sha256": hashlib.sha256((output / (label + ".json")).read_bytes()).hexdigest()}
            for label in reports}, "fixture_sha256": reports["initial"]["fixture_sha256"],
        "limits": reports["initial"]["limits"] + ["Existing independently verified0.30 wheels reused; tests snapshotted from current source",
            "No PostgreSQL, peer process, migration or full-owner-suite claim in this gate"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "tests": totals, "processes": 2}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--installation", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation)
