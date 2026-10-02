"""Independent Knowledge builds, isolated public peers and retained-state replacement."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

from build_tool_images import closure
from check_boundaries import ROOT, project_specs
from postgres_fixture import owned_state

OWNERS = {"knowledge": "amphora-knowledge", "data": "amphora-data-artifacts", "research": "amphora-research"}


def run(command, log, environment=None):
    with log.open("a", encoding="utf-8") as stream:
        result = subprocess.run([str(item) for item in command], stdout=stream, stderr=subprocess.STDOUT,
            env=environment, timeout=600)
    if result.returncode:
        raise RuntimeError(f"Knowledge acceptance failed; inspect {log}")


def timestamp():
    return datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S")


def verify(output):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit retained PostgreSQL fixture opt-in required")
    owned_state()
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    uv = ROOT / (".venv/Scripts/uv.exe" if os.name == "nt" else ".venv/bin/uv")
    specs = {cfg["project"]["name"]: (path, cfg, module) for path, cfg, module in project_specs()}
    manifest = {"timestamp_local": timestamp(), "status": "building", "builds": {}, "tests": {}}
    interpreters = {}

    def save():
        manifest["timestamp_local"] = timestamp()
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    save()
    try:
        for generation in ("initial", "replacement"):
            print(f"Building {generation} owner closures", flush=True)
            wheels = output / generation / "wheels"
            wheels.mkdir(parents=True)
            log = output / (generation + ".log")
            for name in sorted(set.union(*(closure(owner, specs) for owner in OWNERS.values()))):
                run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels], log)
            manifest["builds"][generation] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(wheels.glob("*.whl"))}
            knowledge_wheel = next(wheels.glob("amphora_knowledge-*.whl"))
            with zipfile.ZipFile(knowledge_wheel) as archive:
                names = archive.namelist()
                assert any(name.endswith("r0002_rebuild.sql") for name in names)
                assert not any("/tests/" in name or "fault_host" in name for name in names)
            for label, owner in OWNERS.items():
                print(f"Installing isolated {generation} {label}", flush=True)
                environment = output / generation / label
                requirements = output / generation / (label + ".txt")
                run([uv, "export", "--project", specs[owner][0], "--locked", "--no-dev", "--no-emit-local",
                     "--no-hashes", "--output-file", requirements], log)
                run([uv, "venv", "--python", sys.executable, environment], log)
                python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
                needed = [next(wheels.glob(name.replace("-", "_") + "-*.whl")) for name in sorted(closure(owner, specs))]
                run([uv, "pip", "install", "--python", python, "--constraint", requirements, *needed,
                     "pytest==" + version("pytest"), "httpx==" + version("httpx"),
                     "jsonschema[format-nongpl]==" + version("jsonschema")], log)
                forbidden = [specs[peer][2] for peer in OWNERS.values() if peer != owner]
                probe = ("import importlib.util,pathlib,sys; "
                    f"import {specs[owner][2]} as owner; "
                    f"assert all(importlib.util.find_spec(name) is None for name in {forbidden!r}); "
                    "assert pathlib.Path(owner.__file__).is_relative_to(pathlib.Path(sys.prefix)); "
                    "print('Installed owner excludes peer implementations')")
                run([python, "-I", "-c", probe], log)
                interpreters[generation, label] = python
            save()
        manifest["status"] = "testing"
        save()
        cases = [("initial", ["services/knowledge/tests", "contracts/knowledge/tests"]),
                 ("replacement", ["services/knowledge/tests/api", "services/knowledge/tests/rebuild",
                                  "services/knowledge/tests/acceptance"])]
        for generation, paths in cases:
            key = generation + "-knowledge"
            print(f"Testing {key} against actual isolated Data/Research owners", flush=True)
            evidence = output / key
            evidence.mkdir()
            environment = dict(os.environ, AMPHORA_TEST_POSTGRES="1",
                AMPHORA_TEST_DATA_PYTHON=str(interpreters[generation, "data"]),
                AMPHORA_TEST_RESEARCH_PYTHON=str(interpreters[generation, "research"]),
                AMPHORA_TEST_KNOWLEDGE_PYTHON=str(interpreters["initial", "knowledge"]),
                AMPHORA_TEST_KNOWLEDGE_REPLACEMENT_PYTHON=str(interpreters["replacement", "knowledge"]),
                AMPHORA_KNOWLEDGE_ACCEPTANCE_EVIDENCE=str(evidence / "public-peers.json"),
                AMPHORA_KNOWLEDGE_FAILURE_EVIDENCE=str(evidence / "barriers"))
            report = output / (key + ".xml")
            run([interpreters[generation, "knowledge"], "-I", "-m", "pytest", "-c", ROOT / "dev/pyproject.toml",
                 *[ROOT / path for path in paths], "-q", "--junitxml", report], output / (key + ".log"), environment)
            suites = list(ET.parse(report).getroot().iter("testsuite"))
            totals = {field: sum(int(suite.attrib.get(field, 0)) for suite in suites)
                      for field in ("tests", "failures", "errors", "skipped")}
            assert totals["tests"] > 0 and totals["failures"] == totals["errors"] == totals["skipped"] == 0
            manifest["tests"][key] = totals | {"paths": paths,
                "public_peers": json.loads((evidence / "public-peers.json").read_text(encoding="utf-8")),
                "barriers": [json.loads(path.read_text(encoding="utf-8")) for path in sorted((evidence / "barriers").glob("*.json"))]}
            assert len(manifest["tests"][key]["barriers"]) == 4
            save()
        manifest["status"] = "passed"
        save()
        print(f"Independent Knowledge acceptance passed: {output / 'manifest.json'}", flush=True)
    except Exception:
        manifest["status"] = "failed"
        save()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New output directory; prior results are preserved")
    verify(parser.parse_args().output)
