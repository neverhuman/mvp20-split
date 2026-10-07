"""Hash-checked owner wheel inventory; does not establish service readiness."""

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from ..profile import label, require
from .recipes import OWNERS


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value, reason):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), reason)
    return value


@dataclass(frozen=True)
class WheelIdentity:
    filename: str
    sha256: str

    @classmethod
    def verified(cls, directory, filename, expected):
        require(type(filename) is str and re.fullmatch(r"[A-Za-z0-9_.+-]+\.whl", filename), "installation_wheel_name")
        digest(expected, "installation_wheel_digest")
        path = directory / "wheels" / filename
        require(path.is_file() and sha256(path) == expected, "installation_wheel_content")
        return cls(filename, expected)


@dataclass(frozen=True)
class OwnerInstallation:
    owner: str
    package: str
    release: str
    interpreter_sha256: str
    source_lock_sha256: str
    installation_manifest_sha256: str
    wheels: tuple[WheelIdentity, ...]

    @classmethod
    def from_directory(cls, owner, directory, source_lock):
        require(owner in OWNERS, "installation_owner")
        recipe = OWNERS[owner]
        directory, source_lock = Path(directory), Path(source_lock)
        manifest_path = directory / "manifest.json"
        record = json.loads(manifest_path.read_bytes())
        require(type(record) is dict, "installation_manifest_shape")
        require(record.get("status") == "installed" and record.get("owner") == recipe.package, "installation_manifest_owner")
        packages = record.get("packages")
        require(type(packages) is dict and recipe.package in packages, "installation_packages")
        # This inventory names owner packages, never a combined backend closure.
        foreign = {item.package for item in OWNERS.values()} - {recipe.package}
        require(not foreign.intersection(packages), "installation_private_peer")
        release = label(packages[recipe.package], "installation_release")
        wheels = record.get("wheels")
        require(type(wheels) is dict and 1 <= len(wheels) <= 256, "installation_wheels")
        prefix = recipe.package.replace("-", "_") + "-" + release + "-"
        require(any(name.startswith(prefix) for name in wheels), "installation_owner_wheel")
        verified = tuple(WheelIdentity.verified(directory, name, value) for name, value in sorted(wheels.items()))
        interpreter = directory / "environment/Scripts/python.exe"
        require(interpreter.is_file() and source_lock.is_file(), "installation_local_files")
        return cls(owner, recipe.package, release, sha256(interpreter), sha256(source_lock), sha256(manifest_path), verified)


@dataclass(frozen=True)
class InstallationInventory:
    profile_sha256: str
    source_commit: str
    owners: tuple[OwnerInstallation, ...]

    @classmethod
    def create(cls, profile_sha256, source_commit, owners):
        digest(profile_sha256, "installation_profile_digest")
        require(type(source_commit) is str and re.fullmatch(r"[0-9a-f]{40}", source_commit), "installation_source_commit")
        owners = tuple(owners)
        require(len(owners) == len(OWNERS) and {item.owner for item in owners} == set(OWNERS), "installation_owner_set")
        require(all(item.package == OWNERS[item.owner].package for item in owners), "installation_package_binding")
        return cls(profile_sha256, source_commit, tuple(sorted(owners, key=lambda item: item.owner)))

    def to_record(self):
        return {"schema_version": "1", "profile": "local-owner-inventory-v1", **asdict(self),
                "execution_environment": "native_windows_x86_64_python312", "service_readiness": "not_assessed",
                "scientific_tool_eligibility": "not_assessed", "secrets_included": False}

    def canonical_bytes(self):
        return json.dumps(self.to_record(), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
