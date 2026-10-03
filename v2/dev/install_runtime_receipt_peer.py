"""Build an isolated Runtime receipt peer; installation alone is not integration acceptance."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from build_tool_images import closure
from check_boundaries import ROOT, project_specs


def verify(output):
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
            raise RuntimeError(f"Runtime receipt peer installation failed; inspect {log}")
        return result.stdout if capture else None

    wheels = output / "wheels"
    wheels.mkdir()
    needed = sorted(closure("amphora-campaign-runtime", specs))
    for name in needed:
        run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels])
    constraints = output / "constraints.txt"
    run([uv, "export", "--project", ROOT / "services/campaign_runtime", "--locked", "--no-dev", "--no-emit-local",
         "--no-hashes", "--output-file", constraints])
    run([uv, "venv", "--python", sys.executable, output / "environment"])
    python = output / ("environment/Scripts/python.exe" if os.name == "nt" else "environment/bin/python")
    run([uv, "pip", "install", "--python", python, "--constraint", constraints, *sorted(wheels.glob("*.whl"))])
    run([python, "-I", "-c", "import importlib.util,pathlib,sys; import amphora_campaign_runtime as owner; "
         "assert pathlib.Path(owner.__file__).is_relative_to(pathlib.Path(sys.prefix)); "
         "assert all(importlib.util.find_spec(m) is None for m in "
         "('amphora_data_artifacts','amphora_research','amphora_knowledge'))"])
    manifest = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "installed",
                "scope": "Isolated Runtime receipt peer only; run actual domain receipt integration separately",
                "packages": {name: specs[name][1]["project"]["version"] for name in needed},
                "wheels": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in wheels.glob("*.whl")}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Runtime receipt peer installed: {output / 'manifest.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output)
