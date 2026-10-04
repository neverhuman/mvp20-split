"""Isolated Knowledge processing authorization with retained Data/Research peers."""

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


def verify(output, data_python, research_python, sdk_python):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit retained PostgreSQL fixture opt-in required")
    owned_state()
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    log = output / "verification.log"
    uv = ROOT / ".venv/Scripts/uv.exe"
    specs = {config["project"]["name"]: (path, config, module) for path, config, module in project_specs()}

    def run(command, environment=None):
        result = subprocess.run([str(item) for item in command], env=environment, cwd=output,
                                capture_output=True, text=True, encoding="utf-8", timeout=600)
        with log.open("a", encoding="utf-8") as stream:
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"Knowledge processing verification failed; inspect {log}")

    peers = {"data": data_python.absolute(), "research": research_python.absolute(), "sdk": sdk_python.absolute()}
    for name, package, expected in (("data", "amphora-data-artifacts", "0.29.0"),
                                  ("research", "amphora-research", "0.33.0"), ("sdk", "amphora-tool-protocol", "0.2.0")):
        run([peers[name], "-I", "-c", f"from importlib.metadata import version; assert version('{package}') == '{expected}'"])
    wheels = output / "wheels"
    wheels.mkdir()
    for name in sorted(closure("amphora-knowledge", specs)):
        run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels])
    constraints = output / "constraints.txt"
    run([uv, "export", "--project", ROOT / "services/knowledge", "--locked", "--no-dev", "--no-emit-local",
         "--no-hashes", "--output-file", constraints])
    installations = {}
    for label in ("initial", "replacement"):
        run([uv, "venv", "--python", sys.executable, output / label])
        python = output / label / "Scripts/python.exe"
        run([uv, "pip", "install", "--python", python, "--constraint", constraints, *sorted(wheels.glob("*.whl")),
             "pytest>=8,<9", "httpx>=0.28,<1", "jsonschema>=4.23,<5"])
        run([python, "-I", "-c", "import importlib.util,pathlib,sys; import amphora_knowledge as owner; "
             "from importlib.metadata import version; assert version('amphora-knowledge') == '0.18.0'; "
             "assert pathlib.Path(owner.__file__).absolute().is_relative_to(pathlib.Path(sys.prefix).absolute()); "
             "assert all(importlib.util.find_spec(m) is None for m in "
             "('amphora_data_artifacts','amphora_research','amphora_campaign_runtime','amphora_agent_planning'))"])
        installations[label] = python
    environment = dict(os.environ, PYTHONUTF8="1", AMPHORA_TEST_POSTGRES="1",
        AMPHORA_TEST_DATA_PYTHON=str(peers["data"]), AMPHORA_TEST_DATA_REPLACEMENT_PYTHON=str(peers["data"]),
        AMPHORA_TEST_RESEARCH_PYTHON=str(peers["research"]), AMPHORA_TEST_SDK_PYTHON=str(peers["sdk"]),
        AMPHORA_TEST_KNOWLEDGE_PYTHON=str(installations["initial"]),
        AMPHORA_TEST_KNOWLEDGE_REPLACEMENT_PYTHON=str(installations["replacement"]),
        AMPHORA_KNOWLEDGE_ACCEPTANCE_EVIDENCE=str(output / "public-peers.json"))
    tests = {}
    cases = {"owner": [ROOT / "services/knowledge/tests" / area for area in
                        ("validation", "reasoning", "publication", "api")],
             "actual": [ROOT / "services/knowledge/tests/acceptance/test_public_peers.py"]}
    cases["owner"].append(ROOT / "contracts/knowledge/tests")
    for label, paths in cases.items():
        report = output / (label + ".xml")
        run([installations["initial"], "-I", "-m", "pytest", "-c", ROOT / "dev/pyproject.toml", *paths,
             "--tb=short", "-q", "--junitxml", report], environment)
        totals = {field: sum(int(s.get(field, 0)) for s in ET.parse(report).getroot().iter("testsuite"))
                  for field in ("tests", "failures", "errors", "skipped")}
        assert totals["tests"] > 0 and totals["failures"] == totals["errors"] == totals["skipped"] == 0
        tests[label] = totals
    evidence = json.loads((output / "public-peers.json").read_bytes())
    assert evidence["processing_permission"]["ordinary_read_allowed"]
    assert evidence["processing_permission"]["historical_replay_and_rebuild_stable"]
    manifest = {"status": "passed", "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "knowledge": "0.18.0", "data": "0.29.0", "research": "0.33.0", "tests": tests, "installations": 2,
        "wheels": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(wheels.glob("*.whl"))},
        "evidence": evidence, "limits": ["Synthetic structural/processing permission proof, not scientific validity",
            "Retained compatible peers; no old migrator or fixture reset", "Two installs from one source wheel closure"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "tests": tests, "installations": 2}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data-python", type=Path, required=True)
    parser.add_argument("--research-python", type=Path, required=True)
    parser.add_argument("--sdk-python", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.data_python, args.research_python, args.sdk_python)
