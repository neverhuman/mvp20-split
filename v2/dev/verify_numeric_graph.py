"""Independently install numeric graph owners and exercise real worker HTTP."""

import argparse
import json
import os
import subprocess
from pathlib import Path

from sqlalchemy import URL

from check_boundaries import ROOT
from install_owner_peer import install
from postgres_fixture import owned_state


def verify(output, *, recovery=False, images=None, replacement=False):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit PostgreSQL fixture opt-in required")
    state = owned_state()
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    packages = {"runtime": "amphora-campaign-runtime", "artifact": "amphora-data-artifacts",
                "numeric": "amphora-evolution-search", "evaluator": "amphora-synthetic-objectives", "controller": "amphora-tool-protocol"}
    modules = {"runtime": "amphora_campaign_runtime", "artifact": "amphora_data_artifacts",
               "numeric": "amphora_evolution_search", "evaluator": "amphora_synthetic_objectives"}
    if images is not None:
        packages["registry"] = "amphora-capability-registry"
        modules["registry"] = "amphora_capability_registry"
    interpreters, evidence = {}, {}
    for key, package in packages.items():
        forbidden = tuple(module for name, module in modules.items() if name != key)
        interpreters[key] = str(install(output / key, package, forbidden))
        evidence[key] = json.loads((output / key / "manifest.json").read_bytes())
    replacements = {}
    if replacement:
        for key in ("runtime", "numeric", "evaluator"):
            forbidden = tuple(module for name, module in modules.items() if name != key)
            target = output / (key + "-replacement")
            replacements[key] = str(install(target, packages[key], forbidden))
            evidence[key + "-replacement"] = json.loads((target / "manifest.json").read_bytes())
            assert evidence[key]["wheels"] == evidence[key + "-replacement"]["wheels"]
    config = {**interpreters, "images": None if images is None else str(images.absolute()), "replacements": replacements, "recovery": recovery, "packages": evidence, "evidence": str(output / "http")}
    path = output / "acceptance.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    host, port = state["endpoint"].split(":")
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC"}}
    roles = [("RUNTIME", "runtime_service"), ("ARTIFACT", "artifact_service")]
    if images is not None:
        roles.append(("REGISTRY", "registry_service"))
    for key, role in roles:
        env["AMPHORA_" + key + "_DATABASE_URL"] = URL.create("postgresql+psycopg", username=role,
            password=state["password"], host=host, port=int(port), database=state["database"]).render_as_string(hide_password=False)
    probe = ROOT / "services/campaign_runtime/tests/numeric_search/acceptance/probe.py"
    result = subprocess.run([interpreters["controller"], "-I", str(probe), str(path)], cwd=output,
                            env=env, capture_output=True, text=True, encoding="utf-8", timeout=900)
    (output / "probe.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Numeric HTTP acceptance failed; inspect " + str(output / "probe.log"))
    print(result.stdout, end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--recovery", action="store_true")
    parser.add_argument("--images", type=Path)
    parser.add_argument("--replacement", action="store_true")
    args = parser.parse_args()
    verify(args.output, recovery=args.recovery, images=args.images, replacement=args.replacement)
