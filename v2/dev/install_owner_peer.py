"""Test tooling for a fresh isolated owner build; never confers acceptance."""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime

from build_tool_images import closure
from check_boundaries import ROOT, project_specs


def install(output, package, forbidden):
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
            raise RuntimeError(f"Owner peer installation failed; inspect {log}")
        return result.stdout if capture else None

    wheels = output / "wheels"
    wheels.mkdir()
    needed = sorted(closure(package, specs))
    for name in needed:
        run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels])
    constraints = output / "constraints.txt"
    run([uv, "export", "--project", specs[package][0], "--locked", "--no-dev", "--no-emit-local",
         "--no-hashes", "--output-file", constraints])
    run([uv, "venv", "--python", sys.executable, output / "environment"])
    python = output / ("environment/Scripts/python.exe" if os.name == "nt" else "environment/bin/python")
    run([uv, "pip", "install", "--python", python, "--constraint", constraints, *sorted(wheels.glob("*.whl"))])
    module = specs[package][2]
    probe = ("import importlib,importlib.util,pathlib,sys; owner=importlib.import_module(" + repr(module) + "); "
             "assert pathlib.Path(owner.__file__).is_relative_to(pathlib.Path(sys.prefix)); "
             "assert all(importlib.util.find_spec(m) is None for m in " + repr(tuple(forbidden)) + ")")
    run([python, "-I", "-c", probe])
    manifest = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "installed",
                "scope": "Isolated owner installation only; actual integration/replacement is a separate gate",
                "owner":package,"forbidden_implementations":list(forbidden),
                "packages": {name: specs[name][1]["project"]["version"] for name in needed},
                "wheels": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in wheels.glob("*.whl")}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Owner peer installed: {output / 'manifest.json'}")
    return python

