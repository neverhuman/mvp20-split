"""One local foundation gate; optional isolated wheel builds/install smokes."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from check_boundaries import check, project_specs
from export_schemas import ROOT, publish


def run(command, cwd=None):
    result = subprocess.run([str(c) for c in command], cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        print(result.stdout[-6000:])
        print(result.stderr[-6000:], file=sys.stderr)
        raise SystemExit(result.returncode)
    return result.stdout


def independent_builds(uv):
    specs = list(project_specs())
    # Temporary directory is outside the repository; no source trees are copied/deleted.
    with tempfile.TemporaryDirectory(prefix="amphora-foundation-") as directory:
        root = Path(directory)
        wheels = root / "wheels"
        for project, _, _ in specs:
            run([uv, "build", "--project", project, "--wheel", "--out-dir", wheels])
        for project, config, module in specs:
            name = config["project"]["name"]
            constraints = root / (name + ".txt")
            run(
                [
                    uv,
                    "export",
                    "--project",
                    project,
                    "--locked",
                    "--no-dev",
                    "--no-emit-local",
                    "--no-hashes",
                    "--output-file",
                    constraints,
                ]
            )
            env = root / name
            run([uv, "venv", "--python", sys.executable, env])
            python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            needed = {name}
            pending = list(config.get("tool", {}).get("amphora", {}).get("public-imports", []))
            while pending:
                dependency = pending.pop()
                if dependency in needed:
                    continue
                needed.add(dependency)
                cfg = next(c for _, c, _ in specs if c["project"]["name"] == dependency)
                pending.extend(cfg.get("tool", {}).get("amphora", {}).get("public-imports", []))
            selected = [next(wheels.glob(n.replace("-", "_") + "-*.whl")) for n in sorted(needed)]
            run([uv, "pip", "install", "--python", python, "--constraint", constraints, *selected])
            probe = f"import {module}; import importlib.util; "
            if module.startswith("amphora_contracts_"):
                probe += "assert importlib.util.find_spec('fastapi') is None; "
            elif module == "amphora_campaign_runtime":
                probe += "from amphora_campaign_runtime.api import create_app; assert '/v1/campaign-definitions/validate' in create_app().openapi()['paths']; "
            if module in {"amphora_campaign_runtime", "amphora_data_artifacts"}:
                probe += f"from importlib.resources import files; migration = files('{module}').joinpath('persistence/migrations/versions'); assert any(p.name.endswith('.sql') for p in migration.iterdir()); "
            probe += "assert importlib.util.find_spec('torch') is None; assert importlib.util.find_spec('rdkit') is None"
            run([python, "-I", "-c", probe], cwd=root)
            if module in {"amphora_data_artifacts", "amphora_campaign_runtime"} and os.environ.get("AMPHORA_TEST_POSTGRES") == "1":
                from postgres_fixture import owned_state
                from sqlalchemy import URL
                state = owned_state()
                hostname, port = state["endpoint"].split(":")
                role = "artifact_service" if module == "amphora_data_artifacts" else "runtime_service"
                url = URL.create("postgresql+psycopg", username=role, password=state["password"],
                                 host=hostname, port=int(port), database=state["database"])
                environment = dict(os.environ, AMPHORA_PROBE_DATABASE_URL=url.render_as_string(hide_password=False))
                acceptance = subprocess.run([str(python), "-I", str(project / "tests/acceptance/installed_probe.py")],
                    cwd=root, env=environment, capture_output=True, text=True, timeout=60)
                if acceptance.returncode:
                    raise SystemExit(f"Installed {name} process acceptance failed: " + acceptance.stderr[-2000:])
                print(acceptance.stdout.strip())
            print(f"Independent wheel/install smoke passed: {name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--builds", action="store_true")
    parser.add_argument("--uv", default=shutil.which("uv") or str(ROOT / ".venv/Scripts/uv.exe"))
    args = parser.parse_args()
    findings = check()
    if findings:
        raise SystemExit("\n".join(findings))
    differences = publish(ROOT / "contracts/schemas/v1", check=True)
    if differences:
        raise SystemExit("Schema drift: " + ", ".join(differences))
    print(
        run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--config",
                ROOT / "dev/pyproject.toml",
                ROOT / "contracts",
                ROOT / "services",
                ROOT / "dev",
            ]
        ).strip()
    )
    print(run([sys.executable, ROOT / "dev/run_tests.py"], cwd=ROOT / "dev").strip())
    if args.builds:
        independent_builds(args.uv)
    inventory = [
        {
            "package": cfg["project"]["name"],
            "version": cfg["project"]["version"],
            "path": path.relative_to(ROOT).as_posix(),
            "module": module,
            "public_dependencies": cfg.get("tool", {}).get("amphora", {}).get("public-imports", []),
        }
        for path, cfg, module in project_specs()
    ]
    output = ROOT / "docs/Generated/foundation-packages.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print("Foundation gate passed; package inventory refreshed.")


if __name__ == "__main__":
    main()
