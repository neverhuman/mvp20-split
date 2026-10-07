"""Strict local profile with focused target, storage, access and provider objects."""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit


class ProfileError(ValueError):
    """Safe named configuration error; never includes user values or credentials."""


def require(condition, reason):
    if not condition:
        raise ProfileError(reason)


def fields(value, expected, label):
    require(type(value) is dict and set(value) == set(expected.split()), label + "_fields")
    return value


def label(value, name):
    require(type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value), name)
    return value


def positive(value, name):
    require(type(value) is int and 0 < value <= 2**53 - 1, name)
    return value


def secret_reference(value, name):
    require(type(value) is str and re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", value), name)
    return value


@dataclass(frozen=True)
class Target:
    host_id: str
    operating_system: str
    architecture: str
    python: str
    min_cpu_count: int
    min_memory_bytes: int
    accelerator: str

    @classmethod
    def parse(cls, value):
        v = fields(value, "host_id operating_system architecture python min_cpu_count min_memory_bytes accelerator", "target")
        label(v["host_id"], "target_host")
        require(v["operating_system"] in ("linux", "windows"), "target_system")
        require(v["architecture"] in ("x86_64", "aarch64"), "target_architecture")
        require(v["python"] == "3.12", "target_python")
        positive(v["min_cpu_count"], "target_cpu")
        positive(v["min_memory_bytes"], "target_memory")
        require(v["accelerator"] in ("none", "nvidia"), "target_accelerator")
        return cls(**v)


@dataclass(frozen=True)
class Storage:
    artifact_root: str
    min_free_bytes: int
    durability: str
    verification_ref: str | None

    @classmethod
    def parse(cls, value, target):
        v = fields(value, "artifact_root min_free_bytes durability verification_ref", "storage")
        require(type(v["artifact_root"]) is str and 0 < len(v["artifact_root"]) <= 4096 and "\x00" not in v["artifact_root"], "storage_path")
        path = (PureWindowsPath if target.operating_system == "windows" else PurePosixPath)(v["artifact_root"])
        require(path.is_absolute() and ".." not in path.parts, "storage_absolute_path")
        positive(v["min_free_bytes"], "storage_space")
        require(v["durability"] in ("unverified", "local_durable", "operator_verified_remote"), "storage_durability")
        if v["verification_ref"] is not None:
            label(v["verification_ref"], "storage_verification_reference")
        return cls(**v)


@dataclass(frozen=True)
class Access:
    mode: str
    bind_host: str
    tls: bool
    auth_secret_env: str

    @classmethod
    def parse(cls, value):
        v = fields(value, "mode bind_host tls auth_secret_env", "access")
        require(v["mode"] in ("loopback", "private_lan"), "access_mode")
        import ipaddress
        try:
            ipaddress.ip_address(v["bind_host"])
        except (ValueError, TypeError):
            raise ProfileError("access_bind_address") from None
        require(type(v["bind_host"]) is str and type(v["tls"]) is bool, "access_shape")
        secret_reference(v["auth_secret_env"], "access_secret_reference")
        return cls(**v)


@dataclass(frozen=True)
class Provider:
    mode: str
    endpoint: str | None
    model: str | None
    credential_env: str | None
    budget_usd_micros: int
    data_policy: str

    @classmethod
    def parse(cls, value):
        v = fields(value, "mode endpoint model credential_env budget_usd_micros data_policy", "provider")
        require(v["mode"] in ("disabled", "remote"), "provider_mode")
        require(type(v["budget_usd_micros"]) is int and 0 <= v["budget_usd_micros"] <= 2**53 - 1, "provider_budget")
        require(v["data_policy"] in ("deny", "synthetic_only"), "provider_data_policy")
        if v["mode"] == "disabled":
            require(all(v[k] is None for k in ("endpoint", "model", "credential_env")) and v["budget_usd_micros"] == 0 and v["data_policy"] == "deny", "provider_disabled_fields")
        else:
            require(type(v["endpoint"]) is str and len(v["endpoint"]) <= 2048
                    and not any(character.isspace() or ord(character) < 32 for character in v["endpoint"]), "provider_endpoint")
            try:
                url = urlsplit(v["endpoint"])
                require(url.scheme == "https" and bool(url.hostname) and url.username is None and url.password is None and not url.query and not url.fragment, "provider_endpoint")
                _ = url.port
            except ValueError:
                raise ProfileError("provider_endpoint") from None
            label(v["model"], "provider_model")
            secret_reference(v["credential_env"], "provider_secret_reference")
        return cls(**v)


@dataclass(frozen=True)
class ArtifactCompatibility:
    name: str
    release: str
    sha256: str
    operating_system: str
    architecture: str

    @classmethod
    def parse(cls, value):
        v = fields(value, "name release sha256 operating_system architecture", "artifact")
        label(v["name"], "artifact_name")
        label(v["release"], "artifact_release")
        require(type(v["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", v["sha256"]), "artifact_digest")
        require(v["operating_system"] in ("linux", "windows"), "artifact_system")
        require(v["architecture"] in ("x86_64", "aarch64"), "artifact_architecture")
        return cls(**v)

    def supports(self, target):
        return (self.operating_system, self.architecture) == (target.operating_system, target.architecture)


@dataclass(frozen=True)
class DeploymentProfile:
    schema_version: str
    profile_id: str
    target: Target
    storage: Storage
    access: Access
    provider: Provider
    artifacts: tuple[ArtifactCompatibility, ...]

    @classmethod
    def from_bytes(cls, raw):
        require(type(raw) is bytes and len(raw) <= 65536, "profile_bytes")
        def unique(pairs):
            record = {}
            for key, value in pairs:
                require(key not in record, "profile_duplicate_key")
                record[key] = value
            return record
        try:
            value = json.loads(raw, object_pairs_hook=unique)
        except (ValueError, UnicodeDecodeError, RecursionError) as error:
            if isinstance(error, ProfileError):
                raise
            raise ProfileError("profile_json") from None
        v = fields(value, "schema_version profile_id target storage access provider artifacts", "profile")
        require(v["schema_version"] == "1", "profile_version")
        label(v["profile_id"], "profile_id")
        target = Target.parse(v["target"])
        require(type(v["artifacts"]) is list and 1 <= len(v["artifacts"]) <= 256, "profile_artifacts")
        artifacts = tuple(ArtifactCompatibility.parse(item) for item in v["artifacts"])
        require(len({item.name for item in artifacts}) == len(artifacts), "profile_duplicate_artifact")
        return cls("1", v["profile_id"], target, Storage.parse(v["storage"], target),
                   Access.parse(v["access"]), Provider.parse(v["provider"]), artifacts)

    def canonical_bytes(self):
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

    def credential_names(self):
        names = {self.access.auth_secret_env}
        if self.provider.credential_env is not None:
            names.add(self.provider.credential_env)
        return tuple(sorted(names))
