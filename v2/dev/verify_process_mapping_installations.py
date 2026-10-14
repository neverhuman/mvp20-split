"""Rebuild synthetic process mapping independently; no peer implementation access."""

import argparse
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from check_boundaries import ROOT
from install_owner_peer import install


def verify(output):
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    tests = output / "copied-tests"
    shutil.copytree(ROOT / "tools/process_mapping/tests", tests,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "COMSPEC"}}
    environment["PYTHONUTF8"] = "1"
    uv = ROOT / (".venv/Scripts/uv.exe" if os.name == "nt" else ".venv/bin/uv")
    installations = []
    for label in ("initial", "replacement"):
        python = install(output / label, "amphora-process-mapping", ["amphora_evolution_search", "amphora_campaign_runtime",
            "amphora_data_artifacts", "amphora_research", "amphora_agent_planning"])
        xml = output / (label + ".xml")
        arguments = [str(tests), "--confcutdir=" + str(output), "--import-mode=importlib", "-q", "--tb=short", "--junitxml=" + str(xml)]
        commands = ([uv, "pip", "install", "--python", python, "pytest>=8,<9"],
                    [python, "-I", "-c", "import pytest; raise SystemExit(pytest.main(" + repr(arguments) + "))"])
        for command in commands:
            result = subprocess.run([str(arg) for arg in command], cwd=output, env=environment, capture_output=True,
                text=True, encoding="utf-8", timeout=180, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            with (output / "verification.log").open("a", encoding="utf-8") as stream:
                stream.write(result.stdout + result.stderr)
            assert result.returncode == 0, "Process mapping verification failed; inspect verification.log"
        suites = ET.parse(xml).getroot().findall("testsuite")
        assert suites and all(int(s.attrib[key]) == 0 for s in suites for key in ("errors", "failures", "skipped"))
        installations.append({"label": label, "tests": sum(int(s.attrib["tests"]) for s in suites),
            "installation": json.loads((output / label / "manifest.json").read_bytes())})
        print(json.dumps({"label": label, "tests": installations[-1]["tests"]}), flush=True)
    assert installations[0]["installation"]["wheels"] == installations[1]["installation"]["wheels"]
    (output / "evidence.json").write_text(json.dumps({"verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed", "installations": installations,
        "limits": ["Same source rebuilt twice; not a cross-version migration or worker deployment",
                   "Pure lineage/mapping qualification, not scientific or Runtime acceptance"]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args().output)
