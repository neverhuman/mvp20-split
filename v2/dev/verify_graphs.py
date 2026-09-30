"""Install graph owner/peers independently and prove actual execution plus Runtime replacement."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from sqlalchemy import URL

from build_tool_images import closure
from check_boundaries import ROOT, project_specs
from postgres_fixture import owned_state
from verify_foundation import run


def verify(images, profile="graphs", *, probe_override=None, extra_config=None):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit PostgreSQL fixture opt-in required")
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="runtime_service", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    specs = {config["project"]["name"]: (path, config, module) for path, config, module in project_specs()}
    tool_names = (tuple("amphora-solver-" + stage for stage in ("seed", "select", "mutate", "score", "retain"))
                  if profile in {"solver", "observations"} else ("amphora-numeric-affine", "amphora-sequence-statistics"))
    tool_modules = tuple(specs[name][2] for name in tool_names)
    owners = ("amphora-campaign-runtime", "amphora-capability-registry", "amphora-data-artifacts", "amphora-tool-protocol", *tool_names)
    if profile == "observations":
        owners = (*owners, "amphora-contracts-graph-runtime")
    uv = ROOT / (".venv/Scripts/uv.exe" if os.name == "nt" else ".venv/bin/uv")
    with tempfile.TemporaryDirectory(prefix="amphora-graph-installs-") as directory:
        root = Path(directory)
        wheels = root / "wheels"
        names = sorted(set.union(*(closure(owner, specs) for owner in owners)))
        for name in names:
            run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels])
        installed, replacements = {}, {}
        rebuilding = [owners[0], *(["amphora-contracts-graph-runtime"] if profile == "observations" else [])]
        for owner, replacing in [*((owner, False) for owner in owners), *((owner, True) for owner in rebuilding)]:
            project, _config, module = specs[owner]
            constraints = root / (owner + ".txt")
            run([uv, "export", "--project", project, "--locked", "--no-dev", "--no-emit-local", "--no-hashes", "--output-file", constraints])
            environment = root / (owner + ("-replacement" if replacing else ""))
            run([uv, "venv", "--python", sys.executable, environment])
            python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            needed = [next(wheels.glob(name.replace("-", "_") + "-*.whl")) for name in sorted(closure(owner, specs))]
            run([uv, "pip", "install", "--python", python, "--constraint", constraints, *needed])
            (replacements if replacing else installed)[module] = str(python)
        packages = {wheel.name: hashlib.sha256(wheel.read_bytes()).hexdigest() for wheel in wheels.glob("*.whl")}
        config = root / "acceptance.json"
        observer = ({"observer": installed["amphora_contracts_graph_runtime"],
                     "observer_replacement": replacements["amphora_contracts_graph_runtime"]} if profile == "observations" else {})
        config.write_text(json.dumps({"runtime": installed["amphora_campaign_runtime"], **observer,
            "registry": installed["amphora_capability_registry"], "artifact": installed["amphora_data_artifacts"],
            "tools": {module: installed[module] for module in tool_modules},
            "replacements": replacements, "images": str(images.absolute()),
            "evidence": str(ROOT / {"waits": ".test-results/wait-acceptance", "graphs": ".test-results/graph-acceptance",
                                    "bindings": ".test-results/binding-acceptance", "solver": ".test-results/solver-acceptance",
                                    "observations": ".test-results/observation-acceptance"}[profile]),
            "packages": packages, **(extra_config or {})}), encoding="utf-8")
        env = {key: value for key, value in os.environ.items() if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC", "USERPROFILE", "LOCALAPPDATA", "APPDATA"}}
        for name, role in (("RUNTIME", "runtime_service"), ("ARTIFACT", "artifact_service"), ("REGISTRY", "registry_service")):
            env["AMPHORA_" + name + "_DATABASE_URL"] = url.set(username=role).render_as_string(hide_password=False)
        area = {"waits": "waits", "graphs": "scheduling", "bindings": "bindings", "solver": "baseline", "observations": "graph_inspection"}[profile]
        probe = probe_override or ROOT / f"services/campaign_runtime/tests/{area}/acceptance/probe.py"
        result = subprocess.run([installed["amphora_tool_protocol"], "-I", str(probe), str(config)],
            cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", timeout=600 if profile in {"bindings", "solver", "observations"} else 300)
        print(result.stdout, end="")
        if result.returncode:
            raise SystemExit("Graph acceptance failed: " + result.stderr[-4000:])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", required=True, type=Path)
    parser.add_argument("--profile", choices=("graphs", "waits", "bindings", "solver", "observations"), default="graphs")
    args = parser.parse_args()
    verify(args.images, args.profile)
