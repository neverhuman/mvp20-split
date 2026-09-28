"""Focused installed SDK/tool-owner acceptance without rerunning unrelated owner suites."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from build_tool_images import closure
from check_boundaries import ROOT, project_specs
from postgres_fixture import owned_state
from sqlalchemy import URL
from verify_foundation import run


def verify(images, replacement=False):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit PostgreSQL fixture opt-in required")
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="runtime_service", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    specs = {config["project"]["name"]: (path, config, module) for path, config, module in project_specs()}
    owners = ("amphora-campaign-runtime", "amphora-data-artifacts", "amphora-tool-protocol",
              "amphora-numeric-affine", "amphora-sequence-statistics")
    uv = ROOT / (".venv/Scripts/uv.exe" if os.name == "nt" else ".venv/bin/uv")
    with tempfile.TemporaryDirectory(prefix="amphora-worker-installs-") as directory:
        root = Path(directory)
        wheels = root / "wheels"
        for name in sorted(set.union(*(closure(owner, specs) for owner in owners))):
            run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels])
        installed, replacements = {}, {}
        builds = [(owner, False) for owner in owners]
        if replacement:
            builds.extend((owner, True) for owner in owners[-2:])
        for owner, replacing in builds:
            project, _config, module = specs[owner]
            constraints = root / (owner + ".txt")
            run([uv, "export", "--project", project, "--locked", "--no-dev", "--no-emit-local", "--no-hashes", "--output-file", constraints])
            environment = root / (owner + ("-replacement" if replacing else ""))
            run([uv, "venv", "--python", sys.executable, environment])
            python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            needed = [next(wheels.glob(name.replace("-", "_") + "-*.whl")) for name in sorted(closure(owner, specs))]
            run([uv, "pip", "install", "--python", python, "--constraint", constraints, *needed])
            (replacements if replacing else installed)[module] = str(python)
        config = root / "acceptance.json"
        config.write_text(json.dumps({"runtime": installed["amphora_campaign_runtime"], "artifact": installed["amphora_data_artifacts"],
            "tools": {module: installed[module] for module in ("amphora_numeric_affine", "amphora_sequence_statistics")},
            "replacements": replacements,
            "images": str(Path(images).absolute()), "evidence": str(ROOT / ".test-results/worker-acceptance"),
            "packages": {wheel.name: hashlib.sha256(wheel.read_bytes()).hexdigest() for wheel in wheels.glob("*.whl")}}), encoding="utf-8")
        env = {key: value for key, value in os.environ.items() if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC"}}
        env.update(AMPHORA_RUNTIME_DATABASE_URL=url.render_as_string(hide_password=False),
                   AMPHORA_ARTIFACT_DATABASE_URL=url.set(username="artifact_service").render_as_string(hide_password=False))
        result = subprocess.run([installed["amphora_tool_protocol"], "-I", str(ROOT / "sdk/tool_protocol/tests/acceptance/probe.py"),
            str(config)], cwd=root, env=env, capture_output=True, text=True, timeout=180)
        print(result.stdout, end="")
        if result.returncode:
            raise SystemExit("Worker acceptance failed: " + result.stderr[-3000:])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", required=True, type=Path)
    parser.add_argument("--replacement", action="store_true", help="Prove fresh tool/SDK installs preserve prior owner history")
    arguments = parser.parse_args()
    verify(arguments.images, arguments.replacement)
