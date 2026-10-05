"""Install Planning independently and verify pure context/contract boundaries only."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_tool_images import closure
from check_boundaries import ROOT, project_specs


def verify(output):
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    wheels = output / "wheels"
    wheels.mkdir()
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("AMPHORA_") and key != "PYTHONPATH"}
    environment["PYTHONUTF8"] = "1"
    uv = ROOT / (".venv/Scripts/uv.exe" if os.name == "nt" else ".venv/bin/uv")
    specs = {cfg["project"]["name"]: (path, cfg, module) for path, cfg, module in project_specs()}

    def run(args):
        result = subprocess.run([str(arg) for arg in args], cwd=output, env=environment,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", timeout=120)
        with (output / "build.log").open("a", encoding="utf-8") as stream:
            stream.write(result.stdout)
        if result.returncode:
            raise RuntimeError(f"Planning context acceptance failed; inspect {output / 'build.log'}")

    for name in sorted(closure("amphora-agent-planning", specs)):
        run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels])
    run([uv, "venv", "--python", sys.executable, output / "environment"])
    python = output / ("environment/Scripts/python.exe" if os.name == "nt" else "environment/bin/python")
    run([uv, "pip", "install", "--python", python, *sorted(wheels.glob("*.whl")), "pytest>=8,<9", "jsonschema>=4,<5"])
    run([python, "-I", "-c", "import sys, importlib.util; from pathlib import Path; import amphora_agent_planning; "
         "assert Path(amphora_agent_planning.__file__).absolute().is_relative_to(Path(sys.prefix).absolute()); "
         "assert all(importlib.util.find_spec(n) is None for n in "
         "('amphora_campaign_runtime','amphora_research','amphora_knowledge','amphora_data_artifacts','amphora_capability_registry','fastapi'))"])
    for source, destination in (
        (ROOT / "contracts/planning/tests", output / "tests/contracts"),
        # Retain support modules used by relative test imports; collect only the
        # explicit pure/context/loopback areas below, never persistence tests.
        (ROOT / "services/agent_planning/tests", output / "tests/service"),
    ):
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    areas = [output / "tests/contracts", *(output / "tests/service" / area for area in
        ("context", "campaign_context", "campaign_research_access", "research_view_access", "registry_access", "metadata_reads", "runtime_metadata", "campaign_data_access", "retrieval_access", "campaign_knowledge_access", "campaign_graph_context", "campaign_artifact_context", "campaign_research_context", "graph_context", "proposals", "extraction", "source_access", "knowledge_access",
         "research_access/test_transport.py"))]
    run([python, "-I", "-m", "pytest", *areas, "--import-mode=importlib", "--tb=short", "-q",
         "--junitxml=" + str(output / "tests.xml")])
    suites = ET.parse(output / "tests.xml").getroot().findall("testsuite")
    tests = sum(int(suite.attrib["tests"]) for suite in suites)
    assert tests > 0 and all(int(suite.attrib[key]) == 0 for suite in suites for key in ("errors", "failures", "skipped"))
    manifest = {"verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed", "tests": tests, "seconds": sum(float(suite.attrib["time"]) for suite in suites),
        "planning": specs["amphora-agent-planning"][1]["project"]["version"],
        "contracts": specs["amphora-contracts-planning"][1]["project"]["version"],
        "installations": 1,
        "wheels": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(wheels.glob("*.whl"))},
        "limits": ["Pure context/contract boundary only; loopback HTTP only; no migration, SQL, actual owner service, provider or scientific claim",
                   "Independent installation from current source, not a fresh implementation rewrite"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "tests": tests, "installations": 1}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args().output)
