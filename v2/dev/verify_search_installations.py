"""Two isolated numeric package builds preserve checkpoint bytes and random state."""

import argparse
import hashlib
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
    output.mkdir(parents=True, exist_ok=False)
    tests = output / "numeric-tests"
    shutil.copytree(ROOT / "tools/evolution_search/tests", tests,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "reuse"))
    contracts = output / "contract-tests"
    shutil.copytree(ROOT / "contracts/search/tests", contracts,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    spec = json.loads((tests / "specification/synthetic_specification.json").read_bytes())
    spec["budget"].update(population_size=128, max_evaluations=128)
    specification = output / "original-specification.json"
    specification.write_text(json.dumps(spec), encoding="utf-8")
    retained = output / "retained-checkpoint.json"
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "COMSPEC"}}
    environment["PYTHONUTF8"] = "1"
    records = []

    def run(args):
        result = subprocess.run([str(a) for a in args], cwd=output, env=environment, capture_output=True,
                                text=True, encoding="utf-8", timeout=180,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        with (output / "verification.log").open("a", encoding="utf-8") as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == 0, "Search installation verification failed; inspect verification.log"

    for label in ("initial", "replacement"):
        python = install(output / label, "amphora-evolution-search",
                         ["amphora_campaign_runtime", "amphora_agent_planning", "amphora_research",
                          "amphora_knowledge", "amphora_data_artifacts"])
        uv = ROOT / (".venv/Scripts/uv.exe" if os.name == "nt" else ".venv/bin/uv")
        run([uv, "pip", "install", "--python", python, "pytest>=8,<9", "jsonschema>=4,<5"])
        xml = output / (label + ".xml")
        arguments = [str(tests), str(contracts), "--confcutdir=" + str(output), "--import-mode=importlib",
                     "-q", "--tb=short", "--junitxml=" + str(xml)]
        run([python, "-I", "-c", "import pytest; raise SystemExit(pytest.main(" + repr(arguments) + "))"])
        replay = output / (label + "-replay.json")
        probe = tests / "replacement/replay_probe.py"
        script = ("import runpy; runpy.run_path(" + repr(str(probe)) + ")[\"verify\"]("
                  + ",".join(repr(str(p)) for p in (specification, retained, replay)) + ")")
        run([python, "-I", "-c", script])
        suites = ET.parse(xml).getroot().findall("testsuite")
        assert suites and all(int(s.attrib[key]) == 0 for s in suites for key in ("errors", "failures", "skipped"))
        records.append({"label": label, "tests": sum(int(s.attrib["tests"]) for s in suites),
                        "replay_sha256": hashlib.sha256(replay.read_bytes()).hexdigest(),
                        "installation": json.loads((output / label / "manifest.json").read_bytes())})
        print(json.dumps({"label": label, "tests": records[-1]["tests"], "replay": "passed"}), flush=True)
    assert records[0]["replay_sha256"] == records[1]["replay_sha256"]
    assert records[0]["installation"]["wheels"] == records[1]["installation"]["wheels"]
    evidence = {"verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed",
                "installations": records, "replay": json.loads((output / "replacement-replay.json").read_bytes()),
                "limits": ["No SQL, provider calls or private service implementations",
                           "Identical source rebuilt twice; not a different-version compatibility claim",
                           "Workspace source audit excluded from copied tests; separate retained source-pin proof",
                           "Pending identities are serialized requests, not accepted Runtime invocations"]}
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args().output.absolute())
