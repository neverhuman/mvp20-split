"""Independently build six owner closures; retain a hash-bound native local inventory."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

from amphora_deployment import DeploymentProfile
from amphora_deployment.installation import InstallationInventory, OwnerInstallation, OWNERS

from check_boundaries import ROOT, project_specs
from install_owner_peer import install


def build(output, profile):
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    original = DeploymentProfile.from_bytes(profile.read_bytes())
    specs = {cfg["project"]["name"]: path for path, cfg, _ in project_specs()}
    owners = []
    for name, recipe in OWNERS.items():
        forbidden = [item.module for key, item in OWNERS.items() if key != name]
        forbidden += ["amphora_evolution_search", "amphora_synthetic_objectives", "rdkit", "torch"]
        install(output / "owners" / name, recipe.package, forbidden)
        owners.append(OwnerInstallation.from_directory(name, output / "owners" / name, specs[recipe.package] / "uv.lock"))
    record = json.loads(original.canonical_bytes())
    record["profile_id"] = "local-six-owner-installation"
    record["artifacts"] = []
    for owner in owners:
        for wheel in owner.wheels:
            package, release = wheel.filename.split("-")[:2]
            record["artifacts"].append({"name": owner.owner + "." + package, "release": release, "sha256": wheel.sha256,
                                        "operating_system": "windows", "architecture": "x86_64"})
    selected = DeploymentProfile.from_bytes(json.dumps(record).encode())
    (output / "profile.json").write_bytes(selected.canonical_bytes())
    revision = subprocess.run(["git", "-c", "safe.directory=//DesktopNAS/Code/mvp20-split", "rev-parse", "HEAD"],
                              cwd=ROOT, capture_output=True, text=True, check=True, timeout=15).stdout.strip()
    inventory = InstallationInventory.create(hashlib.sha256(selected.canonical_bytes()).hexdigest(), revision, owners)
    (output / "inventory.json").write_bytes(inventory.canonical_bytes())
    evidence = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed",
        "inventory": inventory.to_record(), "profile_sha256": hashlib.sha256(selected.canonical_bytes()).hexdigest(),
        "inventory_sha256": hashlib.sha256(inventory.canonical_bytes()).hexdigest(),
        "implementation_sha256": {str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT / "deploy/local/src/amphora_deployment/installation").glob("*.py"))},
        "limits": ["Six owner wheel closures installed, not running or database-ready", "No scientific tool eligibility or provider call",
                   "Exact interpreter/local-wheel/lock bytes bound; later runtime tests establish service readiness"], "paid_calls": 0}
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("Six isolated owner closures and immutable local inventory verified", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    args = parser.parse_args()
    build(args.output, args.profile)
