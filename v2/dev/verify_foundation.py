"""One local foundation gate; optional isolated wheel builds/install smokes."""

import argparse
import hashlib
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


def independent_builds(uv, tool_images=None):
    if tool_images is not None and os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        raise ValueError("Tool-owner acceptance requires explicit PostgreSQL fixture opt-in")
    specs = list(project_specs())
    # Temporary directory is outside the repository; no source trees are copied/deleted.
    with tempfile.TemporaryDirectory(prefix="amphora-foundation-") as directory:
        root = Path(directory)
        wheels = root / "wheels"
        installed = {}
        install_recipes = {}
        paired_environment = dict(os.environ)
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
            installed[module] = (python, project)
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
            install_recipes[module] = (constraints, selected)
            run([uv, "pip", "install", "--python", python, "--constraint", constraints, *selected])
            probe = f"import {module}; import importlib.util; "
            if module.startswith("amphora_contracts_"):
                probe += "assert importlib.util.find_spec('fastapi') is None; "
            elif module == "amphora_campaign_runtime":
                probe += "from amphora_campaign_runtime.api import create_app; assert '/v1/campaign-definitions/validate' in create_app().openapi()['paths']; "
            elif module == "amphora_capability_registry":
                probe += "from amphora_capability_registry.descriptors.identity import ReleaseDocument; assert importlib.util.find_spec('amphora_campaign_runtime') is None; assert importlib.util.find_spec('amphora_data_artifacts') is None; "
            if project.parent.name in {"sdk", "tools"}:
                for absent in ("sqlalchemy", "fastapi", "amphora_campaign_runtime", "amphora_data_artifacts", "amphora_capability_registry"):
                    probe += f"assert importlib.util.find_spec('{absent}') is None; "
            if project.parent.name == "tools":
                for sibling in ("amphora_numeric_affine", "amphora_sequence_statistics"):
                    if sibling != module:
                        probe += f"assert importlib.util.find_spec('{sibling}') is None; "
            if module in {"amphora_campaign_runtime", "amphora_data_artifacts"}:
                peer_module = "amphora_data_artifacts" if module == "amphora_campaign_runtime" else "amphora_campaign_runtime"
                probe += f"assert importlib.util.find_spec('{peer_module}') is None; "
                probe += f"from importlib.resources import files; migration = files('{module}').joinpath('persistence/migrations/versions'); assert any(p.name.endswith('.sql') for p in migration.iterdir()); "
            probe += "assert importlib.util.find_spec('torch') is None; assert importlib.util.find_spec('rdkit') is None"
            run([python, "-I", "-c", probe], cwd=root)
            if project.parent.name == "tools":
                golden = json.loads((project / "tests/fixtures/golden.json").read_bytes())
                checked = subprocess.run([str(python), "-I", "-m", module, "compute"], cwd=root,
                    input=json.dumps(golden["input"]), text=True, capture_output=True, timeout=20)
                if checked.returncode or json.loads(checked.stdout) != golden["output"]:
                    raise SystemExit("Installed tool golden behavior failed: " + module)
                release = json.loads(run([python, "-I", "-m", module, "describe", "--image-sha256", "c" * 64], cwd=root))
                if release["tool"]["binding"]["release"] != config["project"]["version"] or release["authority_ceiling"] != "synthetic_only":
                    raise SystemExit("Installed tool descriptor mismatch: " + module)
                print(f"Installed standalone tool kernel/schema/descriptor passed: {module}; test-only image pin")
            if module in {"amphora_data_artifacts", "amphora_campaign_runtime"} and os.environ.get("AMPHORA_TEST_POSTGRES") == "1":
                from postgres_fixture import owned_state
                from sqlalchemy import URL
                state = owned_state()
                hostname, port = state["endpoint"].split(":")
                role = "artifact_service" if module == "amphora_data_artifacts" else "runtime_service"
                url = URL.create("postgresql+psycopg", username=role, password=state["password"],
                                 host=hostname, port=int(port), database=state["database"])
                environment = dict(os.environ, AMPHORA_PROBE_DATABASE_URL=url.render_as_string(hide_password=False))
                key = "AMPHORA_ARTIFACT_DATABASE_URL" if module == "amphora_data_artifacts" else "AMPHORA_RUNTIME_DATABASE_URL"
                paired_environment[key] = url.render_as_string(hide_password=False)
                migration_key = "AMPHORA_ARTIFACT_MIGRATION_URL" if module == "amphora_data_artifacts" else "AMPHORA_RUNTIME_MIGRATION_URL"
                paired_environment[migration_key] = url.set(username=role.replace("_service", "_migrator")).render_as_string(hide_password=False)
                acceptance = subprocess.run([str(python), "-I", str(project / "tests/acceptance/installed_probe.py")],
                    cwd=root, env=environment, capture_output=True, text=True, timeout=60)
                if acceptance.returncode:
                    raise SystemExit(f"Installed {name} process acceptance failed: " + acceptance.stderr[-2000:])
                print(acceptance.stdout.strip())
            print(f"Independent wheel/install smoke passed: {name}")
        registry_python, registry_project = installed["amphora_capability_registry"]
        registry_probe = registry_project / "tests/acceptance/installed_probe.py"
        registry_replacement = root / "registry-replacement"
        run([uv, "venv", "--python", sys.executable, registry_replacement])
        replacement_python = registry_replacement / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        constraints, selected = install_recipes["amphora_capability_registry"]
        run([uv, "pip", "install", "--python", replacement_python, "--constraint", constraints, *selected])
        fixture_cases = json.loads((ROOT / "contracts/fixtures/v1/tool_releases.json").read_text())
        for fixture in fixture_cases:
            previous = None
            for executable in (registry_python, replacement_python):
                request = fixture if previous is None else json.loads(previous)
                checked = subprocess.run([str(executable), "-I", str(registry_probe)], cwd=root,
                    input=json.dumps(request) + "\n", capture_output=True, text=True, timeout=20)
                if checked.returncode:
                    raise SystemExit("Installed registry descriptor proof failed: " + checked.stderr[-2000:])
                if previous is not None:
                    assert checked.stdout == previous, "Replacement changed descriptor lock or policy decision"
                previous = checked.stdout
        print("Installed registry: both golden descriptors, canonical locks and decisions preserved across fresh replacement")
        if os.environ.get("AMPHORA_TEST_POSTGRES") == "1":
            from postgres_fixture import registry_owner
            registry_owner(state)
            registry_url = url.set(username="registry_service")
            registry_environment = dict(os.environ,
                AMPHORA_REGISTRY_DATABASE_URL=registry_url.render_as_string(hide_password=False),
                AMPHORA_REGISTRY_MIGRATION_URL=registry_url.set(username="registry_migrator").render_as_string(hide_password=False),
                AMPHORA_TESTED_PACKAGES=json.dumps({w.name: hashlib.sha256(w.read_bytes()).hexdigest() for w in wheels.glob("*.whl")}))
            acceptance = subprocess.run([str(registry_python), "-I", str(registry_project / "tests/acceptance/service_probe.py"),
                str(replacement_python), str(ROOT / "contracts/fixtures/v1/tool_releases.json"), str(ROOT / ".test-results/registry-replacement")],
                cwd=root, env=registry_environment, capture_output=True, text=True, timeout=90)
            if acceptance.returncode:
                raise SystemExit("Installed registry HTTP replacement failed: " + acceptance.stderr[-2500:])
            print(acceptance.stdout.strip())
        paired_environment["AMPHORA_REGISTRY_PROBE_PYTHON"] = str(registry_python)
        paired_environment["AMPHORA_REGISTRY_PROBE_SCRIPT"] = str(registry_probe)
        if os.environ.get("AMPHORA_TEST_POSTGRES") == "1":
            runtime_python, runtime_project = installed["amphora_campaign_runtime"]
            artifact_python, _ = installed["amphora_data_artifacts"]
            acceptance = subprocess.run([str(runtime_python), "-I",
                str(runtime_project / "tests/acceptance/integrated_probe.py"), str(artifact_python)],
                cwd=root, env=paired_environment, capture_output=True, text=True, timeout=120)
            if acceptance.returncode:
                raise SystemExit("Installed paired acceptance failed: " + acceptance.stderr[-3500:])
            print(acceptance.stdout.strip())
            artifact_project = installed["amphora_data_artifacts"][1]
            evidence_dir = ROOT / ".test-results/recovery"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            paired_environment["AMPHORA_TESTED_PACKAGES"] = json.dumps({w.name: hashlib.sha256(w.read_bytes()).hexdigest()
                                                                      for w in wheels.glob("*.whl")})
            for module, label in (("amphora_campaign_runtime", "RUNTIME"), ("amphora_data_artifacts", "ARTIFACT")):
                replacement = root / (module + "-replacement")
                run([uv, "venv", "--python", sys.executable, replacement])
                replacement_python = replacement / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
                constraints, selected = install_recipes[module]
                run([uv, "pip", "install", "--python", replacement_python, "--constraint", constraints, *selected])
                paired_environment["AMPHORA_REPLACEMENT_" + label + "_PYTHON"] = str(replacement_python)
            recovery = subprocess.run([str(runtime_python), "-I", str(runtime_project / "tests/acceptance/integrated_probe.py"),
                str(artifact_python), str(artifact_project / "tests/acceptance/fault_host.py"), str(evidence_dir)],
                cwd=root, env=paired_environment, capture_output=True, text=True, timeout=180)
            if recovery.returncode:
                raise SystemExit("Installed recovery acceptance failed: " + recovery.stderr[-4000:])
            print(recovery.stdout.strip())
            if tool_images is not None:
                sdk_python, sdk_project = installed["amphora_tool_protocol"]
                worker_config = root / "worker-acceptance.json"
                worker_config.write_text(json.dumps({"runtime": str(runtime_python), "artifact": str(artifact_python),
                    "tools": {module: str(installed[module][0]) for module in ("amphora_numeric_affine", "amphora_sequence_statistics")},
                    "images": str(Path(tool_images).absolute()), "evidence": str(ROOT / ".test-results/worker-acceptance"),
                    "packages": json.loads(paired_environment["AMPHORA_TESTED_PACKAGES"])}), encoding="utf-8")
                worker_environment = {key: value for key, value in paired_environment.items() if key.upper() in {
                    "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC", "AMPHORA_RUNTIME_DATABASE_URL", "AMPHORA_ARTIFACT_DATABASE_URL"}}
                acceptance = subprocess.run([str(sdk_python), "-I", str(sdk_project / "tests/acceptance/probe.py"), str(worker_config)],
                    cwd=root, env=worker_environment, capture_output=True, text=True, timeout=180)
                if acceptance.returncode:
                    raise SystemExit("Installed worker/owner acceptance failed: " + acceptance.stdout[-1000:] + acceptance.stderr[-3500:])
                print(acceptance.stdout.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--builds", action="store_true")
    parser.add_argument("--tool-images", type=Path)
    parser.add_argument("--uv", default=shutil.which("uv") or str(ROOT / ".venv/Scripts/uv.exe"))
    args = parser.parse_args()
    if args.tool_images is not None and not args.builds:
        parser.error("--tool-images requires --builds")
    findings = check()
    if findings:
        raise SystemExit("\n".join(findings))
    differences = [f"v{version}/{name}" for version in ("1", "2")
        for name in publish(ROOT / ("contracts/schemas/v" + version), check=True, version=version)]
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
                ROOT / "sdk",
                ROOT / "tools",
                ROOT / "dev",
                ROOT / "tests/integration",
            ]
        ).strip()
    )
    print(run([sys.executable, ROOT / "dev/run_tests.py"], cwd=ROOT / "dev").strip())
    if args.builds:
        independent_builds(args.uv, args.tool_images)
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
