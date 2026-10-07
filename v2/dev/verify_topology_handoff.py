"""Public topology handoff using preserved independent owner installations."""

import argparse
import json
import os
import subprocess
from pathlib import Path

from sqlalchemy import URL

from check_boundaries import ROOT
from postgres_fixture import owned_state


def verify(output, installs, runtime, benchmark, images=None, replacements=None):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit owned PostgreSQL fixture opt-in required")
    state = owned_state()
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    interpreters, manifests = {}, {}
    for owner in ("runtime", "artifact", "planning", "registry", "controller", "numeric-old", "numeric-new"):
        location = runtime.absolute() if owner == "runtime" else installs.absolute() / owner
        manifests[owner] = json.loads((location / "manifest.json").read_bytes())
        assert manifests[owner]["status"] == "installed"
        interpreters[owner] = str(location / ("environment/Scripts/python.exe" if os.name == "nt" else "environment/bin/python"))
    assert manifests["runtime"]["packages"]["amphora-campaign-runtime"] == "0.65.0"
    assert manifests["planning"]["packages"]["amphora-agent-planning"] == "0.98.0"
    replacement_paths = {}
    if replacements is not None:
        for owner in ("planning", "runtime", "numeric-new"):
            location = replacements.absolute() / owner
            manifest = json.loads((location / "manifest.json").read_bytes())
            assert manifest["status"] == "installed" and manifest["packages"] == manifests[owner]["packages"]
            manifests[owner + "-replacement"] = manifest
            replacement_paths[owner] = str(location / ("environment/Scripts/python.exe" if os.name == "nt" else "environment/bin/python"))
    config = {**interpreters, "packages": manifests, "benchmark": str(benchmark.absolute()), "evidence": str(output / "http"),
              "images": None if images is None else str(images.absolute()), "replacements": replacement_paths}
    path = output / "acceptance.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    host, port = state["endpoint"].split(":")
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC"}}
    env["PYTHONUTF8"] = "1"
    for owner in ("runtime", "artifact", "planning", "registry"):
        env["AMPHORA_" + owner.upper() + "_DATABASE_URL"] = URL.create("postgresql+psycopg", username=owner + "_service",
            password=state["password"], host=host, port=int(port), database=state["database"]).render_as_string(hide_password=False)
    probe = ROOT / "services/agent_planning/tests/topology/acceptance/probe.py"
    result = subprocess.run([interpreters["controller"], "-I", str(probe), str(path)], cwd=output,
                            env=env, capture_output=True, text=True, encoding="utf-8", timeout=900)
    (output / "probe.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Topology handoff failed; inspect " + str(output / "probe.log"))
    print(result.stdout, end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("output", "installs", "runtime", "benchmark"):
        parser.add_argument("--" + option, required=True, type=Path)
    parser.add_argument("--images", type=Path)
    parser.add_argument("--replacements", type=Path)
    args = parser.parse_args()
    verify(args.output, args.installs, args.runtime, args.benchmark, args.images, args.replacements)
