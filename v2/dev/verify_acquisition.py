"""Independent Data/Research installations, actual peers and immutable-history cutover."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

from build_tool_images import closure
from check_boundaries import ROOT, project_specs
from postgres_fixture import owned_state

OWNERS = {"data": "amphora-data-artifacts", "research": "amphora-research"}


def run(command, log, environment=None):
    with log.open("a", encoding="utf-8") as stream:
        result = subprocess.run([str(item) for item in command], stdout=stream, stderr=subprocess.STDOUT,
                                env=environment, timeout=600)
    if result.returncode:
        raise RuntimeError(f"Acquisition acceptance failed; inspect {log}")


def verify(output):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit retained PostgreSQL fixture opt-in required")
    owned_state()  # Validate the retained fixture; never reset it.
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    uv = ROOT / (".venv/Scripts/uv.exe" if os.name == "nt" else ".venv/bin/uv")
    specs = {cfg["project"]["name"]: (path, cfg, module) for path, cfg, module in project_specs()}
    manifest = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "building", "builds": {}, "tests": {}}
    interpreters = {}
    for generation in ("initial", "replacement"):
        print(f"Building {generation} owner closures", flush=True)
        wheels = output / generation / "wheels"
        wheels.mkdir(parents=True)
        log = output / (generation + ".log")
        for name in sorted(set.union(*(closure(owner, specs) for owner in OWNERS.values()))):
            run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels], log)
        manifest["builds"][generation] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                          for path in sorted(wheels.glob("*.whl"))}
        for label, owner in OWNERS.items():
            environment = output / generation / label
            requirements = output / generation / (label + ".txt")
            run([uv, "export", "--project", specs[owner][0], "--locked", "--no-dev", "--no-emit-local",
                 "--no-hashes", "--output-file", requirements], log)
            run([uv, "venv", "--python", sys.executable, environment], log)
            python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            needed = [next(wheels.glob(name.replace("-", "_") + "-*.whl")) for name in sorted(closure(owner, specs))]
            run([uv, "pip", "install", "--python", python, "--constraint", requirements,
                 *needed, "pytest==" + version("pytest"), "httpx==" + version("httpx")], log)
            forbidden = "amphora_research" if label == "data" else "amphora_data_artifacts"
            probe = ("import importlib.util, pathlib, sys; "
                     f"import {specs[owner][2]} as owner; "
                     f"assert importlib.util.find_spec('{forbidden}') is None; "
                     "assert pathlib.Path(owner.__file__).is_relative_to(pathlib.Path(sys.prefix)); "
                     "print('Isolated installed owner verified')")
            run([python, "-I", "-c", probe], log)
            interpreters[generation, label] = python
    manifest["status"] = "testing"
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    environment = dict(os.environ,
        AMPHORA_TEST_RESEARCH_PYTHON=str(interpreters["initial", "research"]),
        AMPHORA_TEST_RESEARCH_REPLACEMENT_PYTHON=str(interpreters["replacement", "research"]),
        AMPHORA_TEST_DATA_REPLACEMENT_PYTHON=str(interpreters["replacement", "data"]))
    cases = [
        ("data", "initial", ["services/data_artifacts/tests/acquisition", "services/data_artifacts/tests/source_rights"]),
        ("research", "initial", ["services/research/tests"]),
        ("research", "replacement", ["services/research/tests/api"]),
    ]
    for label, generation, paths in cases:
        key = generation + "-" + label
        print(f"Testing {key} with actual retained PostgreSQL and public peers", flush=True)
        log = output / (key + "-tests.log")
        try:
            run([interpreters[generation, label], "-I", "-m", "pytest", "-c", ROOT / "dev/pyproject.toml",
                 *[ROOT / path for path in paths], "-q", "--junitxml", output / (key + ".xml")], log, environment)
        except (RuntimeError, subprocess.TimeoutExpired):
            manifest["status"] = "failed"
            manifest["tests"][key] = {"result": "failed", "paths": paths}
            (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            raise
        manifest["tests"][key] = {"result": "passed", "paths": paths}
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["status"] = "passed"
    manifest["timestamp_local"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    manifest["qev"] = json.loads((ROOT / ".test-results/bp0601-qev.json").read_text(encoding="utf-8"))
    manifest["recovery"] = [json.loads(path.read_text(encoding="utf-8"))
                            for path in sorted((ROOT / ".test-results/bp0601-process-recovery").glob("*.json"))]
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Independent acquisition acceptance passed: {output / 'manifest.json'}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New output directory; existing results are preserved")
    verify(parser.parse_args().output)
