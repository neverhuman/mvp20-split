"""Independently install Knowledge and verify correction/publication boundaries against owner PostgreSQL."""

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


def verify(output):
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
            raise RuntimeError(f"Knowledge correction verification failed; inspect {log}")
        return result.stdout if capture else None

    wheels = output / "wheels"
    wheels.mkdir()
    needed = sorted(closure("amphora-knowledge", specs))
    for name in needed:
        run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels])
    constraints = output / "constraints.txt"
    run([uv, "export", "--project", ROOT / "services/knowledge", "--locked", "--no-dev", "--no-emit-local",
         "--no-hashes", "--output-file", constraints])
    run([uv, "venv", "--python", sys.executable, output / "environment"])
    python = output / ("environment/Scripts/python.exe" if os.name == "nt" else "environment/bin/python")
    run([uv, "pip", "install", "--python", python, "--constraint", constraints, *sorted(wheels.glob("*.whl")),
         "pytest>=8,<9", "httpx>=0.28,<1", "jsonschema>=4.23,<5"])
    run([python, "-I", "-c", "import importlib.util,pathlib,sys; import amphora_knowledge as owner; "
         "assert pathlib.Path(owner.__file__).is_relative_to(pathlib.Path(sys.prefix)); "
         "assert all(importlib.util.find_spec(m) is None for m in "
         "('amphora_data_artifacts','amphora_research','amphora_campaign_runtime'))"])
    environment = dict(os.environ, PYTHONUTF8="1")
    run([python, "-I", "-m", "pytest", "-c", ROOT / "dev/pyproject.toml", ROOT / "services/knowledge/tests/corrections", ROOT / "services/knowledge/tests/publication",
         ROOT / "contracts/knowledge/tests", "-q", "--tb=short", "--junitxml", output / "tests.xml"], environment)
    totals = {field: sum(int(s.get(field, 0)) for s in ET.parse(output / "tests.xml").getroot().iter("testsuite"))
              for field in ("tests", "failures", "errors", "skipped")}
    assert totals["tests"] > 0 and totals["failures"] == totals["errors"] == totals["skipped"] == 0
    manifest = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed",
                "scope": "Installed Knowledge correction/publication and public-contract suites; real owner SQL, synthetic publication peers; no actual remote-peer or kill-barrier claim",
                "tests": totals,
                "packages": {name: specs[name][1]["project"]["version"] for name in needed},
                "wheels": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in wheels.glob("*.whl")}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Installed Knowledge correction verification passed: {totals}; {output / 'manifest.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output)
