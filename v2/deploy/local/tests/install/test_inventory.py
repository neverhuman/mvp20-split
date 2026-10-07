"""Exact owner closure identity and explicit non-readiness claims."""

import hashlib
import json
from dataclasses import replace

import pytest

from amphora_deployment import ProfileError
from amphora_deployment.installation import OWNERS, InstallationInventory, OwnerInstallation


@pytest.fixture
def installed(tmp_path):
    name = "amphora_campaign_runtime-0.65.0-py3-none-any.whl"
    (tmp_path / "wheels").mkdir()
    (tmp_path / "wheels" / name).write_bytes(b"synthetic unit wheel")
    (tmp_path / "environment/Scripts").mkdir(parents=True)
    (tmp_path / "environment/Scripts/python.exe").write_bytes(b"synthetic unit interpreter")
    lock = tmp_path / "source.lock"
    lock.write_bytes(b"synthetic locked closure")
    manifest = {"status": "installed", "owner": "amphora-campaign-runtime", "packages": {"amphora-campaign-runtime": "0.65.0"},
                "wheels": {name: hashlib.sha256(b"synthetic unit wheel").hexdigest()}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    return tmp_path, lock, manifest


def test_exact_files_and_stable_inventory_order(installed):
    root, lock, _ = installed
    item = OwnerInstallation.from_directory("runtime", root, lock)
    items = [replace(item, owner=owner, package=recipe.package) for owner, recipe in OWNERS.items()]
    first = InstallationInventory.create("a" * 64, "b" * 40, items)
    assert first.canonical_bytes() == InstallationInventory.create("a" * 64, "b" * 40, reversed(items)).canonical_bytes()
    assert first.to_record()["service_readiness"] == first.to_record()["scientific_tool_eligibility"] == "not_assessed"
    assert first.to_record()["secrets_included"] is False
    assert item.source_lock_sha256 == hashlib.sha256(lock.read_bytes()).hexdigest()
    with pytest.raises(ProfileError, match="installation_package_binding"):
        InstallationInventory.create("a" * 64, "b" * 40, [replace(entry, package="wrong") for entry in items])


def test_changed_wheel_fails_before_inventory(installed):
    root, lock, manifest = installed
    (root / "wheels" / next(iter(manifest["wheels"]))).write_bytes(b"changed")
    with pytest.raises(ProfileError, match="installation_wheel_content"):
        OwnerInstallation.from_directory("runtime", root, lock)


@pytest.mark.parametrize("mutation,reason", [
    (lambda m: m.update(owner="amphora-research"), "installation_manifest_owner"),
    (lambda m: m["packages"].update({"amphora-data-artifacts": "0.30.0"}), "installation_private_peer"),
    (lambda m: m.update(wheels={}), "installation_wheels"),
    (lambda m: m["wheels"].update({"../escape.whl": "a" * 64}), "installation_wheel_name"),
    (lambda m: m["packages"].update({"amphora-campaign-runtime": "0.64.0"}), "installation_owner_wheel"),
])
def test_invalid_closure_is_rejected(installed, mutation, reason):
    root, lock, manifest = installed
    mutation(manifest)
    (root / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ProfileError, match=reason):
        OwnerInstallation.from_directory("runtime", root, lock)


def test_missing_duplicate_or_invalid_identity(installed):
    root, lock, _ = installed
    item = OwnerInstallation.from_directory("runtime", root, lock)
    for items in ([], [item] * 6):
        with pytest.raises(ProfileError, match="installation_owner_set"):
            InstallationInventory.create("a" * 64, "b" * 40, items)
    with pytest.raises(ProfileError, match="installation_profile_digest"):
        InstallationInventory.create("bad", "b" * 40, [])


def test_commands_are_owner_fixed_and_migrations_separate():
    for name, recipe in OWNERS.items():
        migration = recipe.migration_command("python.exe")
        server = recipe.serve_command("python.exe", "owner.json", 18100)
        assert migration[3] == recipe.module + ".persistence.migrate"
        assert recipe.migration_role != recipe.service_role
        assert recipe.migration_environment not in server and "migrate" not in server
        if name == "planning":
            assert server[3] == "amphora_agent_planning.supervision_api"
            assert server[server.index("--host") + 1] == "127.0.0.1"
        else:
            assert server[3:6] == (recipe.module, "serve", "--config")
        with pytest.raises(ProfileError, match="installation_port"):
            recipe.serve_command("python.exe", "owner.json", True)
