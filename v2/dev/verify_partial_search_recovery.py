"""Actual partial-evaluation recovery through a public-only isolated controller."""

import argparse
import json
import os
import subprocess
from pathlib import Path

from sqlalchemy import URL

from check_boundaries import ROOT
from install_owner_peer import install
from postgres_fixture import owned_state


def verify(args):
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Explicit owned PostgreSQL fixture opt-in required")
    state = owned_state()
    dependencies = args.dependencies.absolute()
    for key, package in (("evaluator", "amphora-synthetic-objectives"), ("controller", "amphora-contracts-search-steps")):
        path = dependencies / key
        if not path.exists():
            install(path, package, ["sqlalchemy", "amphora_campaign_runtime", "amphora_agent_planning", "amphora_data_artifacts", "amphora_evolution_search"])
    locations = {key: getattr(args, key).absolute() for key in ("runtime", "artifact", "numeric", "replacement_runtime")}
    locations.update({key: dependencies / key for key in ("evaluator", "controller")})
    if args.scenario == "correction":
        if args.corrected_evaluator is None:
            raise ValueError("Correction scenario requires a preserved separate evaluator installation")
        locations["evaluator_corrected"] = args.corrected_evaluator.absolute()
    interpreters, packages = {}, {}
    for key, path in locations.items():
        packages[key] = json.loads((path / "manifest.json").read_bytes())
        assert packages[key]["status"] == "installed"
        interpreters[key] = str(path / ("environment/Scripts/python.exe" if os.name == "nt" else "environment/bin/python"))
    assert packages["runtime"]["packages"]["amphora-campaign-runtime"] == packages["replacement_runtime"]["packages"]["amphora-campaign-runtime"] == "0.65.0"
    assert packages["numeric"]["packages"]["amphora-evolution-search"] == "0.5.0"
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    config = {**interpreters, "packages": packages, "evidence": str(output / "http"),
              "reconstructed_adapter": str(ROOT / "tests/integration/search_recovery/rebuilt_adapter.py")}
    path = output / "acceptance.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    env = {key:value for key,value in os.environ.items() if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC"}}
    env["PYTHONUTF8"] = "1"
    host, port = state["endpoint"].split(":")
    for owner in ("runtime", "artifact"):
        env["AMPHORA_" + owner.upper() + "_DATABASE_URL"] = URL.create("postgresql+psycopg", username=owner + "_service",
            password=state["password"], host=host, port=int(port), database=state["database"]).render_as_string(hide_password=False)
    probe = "correction_probe.py" if args.scenario == "correction" else "probe.py"
    result = subprocess.run([interpreters["controller"], "-I", str(ROOT / "tests/integration/search_recovery" / probe), str(path)],
                            cwd=output, env=env, capture_output=True, timeout=900)
    (output / "probe.log").write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, "Partial search recovery failed; inspect probe.log"
    print(result.stdout.decode(), end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("output", "dependencies", "runtime", "artifact", "numeric", "replacement-runtime"):
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--scenario", choices=("partial", "correction"), default="partial")
    parser.add_argument("--corrected-evaluator", type=Path)
    verify(parser.parse_args())
