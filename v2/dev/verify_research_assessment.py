"""Independently install Research and exercise resolution against retained installed public peers."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from build_tool_images import closure
from check_boundaries import ROOT, project_specs
from postgres_fixture import owned_state


def verify(output, data_python, knowledge_python):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit retained PostgreSQL fixture opt-in required")
    owned_state()
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    log = output / "verification.log"
    uv = ROOT / (".venv/Scripts/uv.exe" if os.name == "nt" else ".venv/bin/uv")
    specs = {cfg["project"]["name"]: (path, cfg, module) for path, cfg, module in project_specs()}

    def run(command, environment=None, capture=False):
        result = subprocess.run([str(item) for item in command], env=environment,
                                capture_output=True, text=True, encoding="utf-8", timeout=300)
        with log.open("a", encoding="utf-8") as stream:
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"Research verification failed; inspect {log}")
        return result.stdout if capture else None

    peers = {}
    for label, interpreter, module, package in [
        ("data", data_python, "amphora_data_artifacts", "amphora-data-artifacts"),
        ("knowledge", knowledge_python, "amphora_knowledge", "amphora-knowledge"),
    ]:
        probe = ("import importlib.util,json,pathlib,sys; from importlib.metadata import version; "
                 f"import {module} as owner; "
                 "assert pathlib.Path(owner.__file__).is_relative_to(pathlib.Path(sys.prefix)); "
                 "assert importlib.util.find_spec('amphora_research') is None; "
                 f"print(json.dumps({{'package':'{package}','version':version('{package}')}}))")
        peers[label] = json.loads(run([interpreter.absolute(), "-I", "-c", probe], capture=True))
    wheels = output / "wheels"
    wheels.mkdir()
    needed = sorted(closure("amphora-research", specs))
    for name in needed:
        run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels])
    constraints = output / "constraints.txt"
    run([uv, "export", "--project", ROOT / "services/research", "--locked", "--no-dev", "--no-emit-local",
         "--no-hashes", "--output-file", constraints])
    run([uv, "venv", "--python", sys.executable, output / "environment"])
    python = output / ("environment/Scripts/python.exe" if os.name == "nt" else "environment/bin/python")
    run([uv, "pip", "install", "--python", python, "--constraint", constraints, *sorted(wheels.glob("*.whl")),
         "pytest>=8,<9", "httpx>=0.28,<1", "jsonschema>=4.23,<5"])
    run([python, "-I", "-c", "import importlib.util,pathlib,sys; import amphora_research as owner; "
         "assert pathlib.Path(owner.__file__).is_relative_to(pathlib.Path(sys.prefix)); "
         "assert all(importlib.util.find_spec(m) is None for m in "
         "('amphora_data_artifacts','amphora_knowledge','amphora_campaign_runtime'))"])
    environment = dict(os.environ, PYTHONUTF8="1", AMPHORA_TEST_DATA_PYTHON=str(data_python.absolute()),
                       AMPHORA_TEST_KNOWLEDGE_PYTHON=str(knowledge_python.absolute()),
                       AMPHORA_RESEARCH_RESOLUTION_EVIDENCE=str(output / "actual-peers.json"))
    run([python, "-I", "-m", "pytest", "-c", ROOT / "dev/pyproject.toml", ROOT / "services/research/tests",
         ROOT / "contracts/research/tests", "-q", "--tb=short", "--junitxml", output / "tests.xml"], environment)
    totals = {field: sum(int(s.get(field, 0)) for s in ET.parse(output / "tests.xml").getroot().iter("testsuite"))
              for field in ("tests", "failures", "errors", "skipped")}
    assert totals["tests"] > 0 and totals["failures"] == totals["errors"] == totals["skipped"] == 0
    manifest = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed",
                "scope": "B1.09 installed Research resolution, immutable assessment storage and publication; not public assessment API",
                "peers": peers, "tests": totals,
                "packages": {name: specs[name][1]["project"]["version"] for name in needed},
                "wheels": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in wheels.glob("*.whl")},
                "actual_peers": json.loads((output / "actual-peers.json").read_text(encoding="utf-8"))}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Installed Research verification passed: {totals}; {output / 'manifest.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data-python", type=Path, required=True)
    parser.add_argument("--knowledge-python", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.data_python, args.knowledge_python)
