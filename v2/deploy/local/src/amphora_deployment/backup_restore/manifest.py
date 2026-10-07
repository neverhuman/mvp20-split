"""Versioned immutable snapshot description, with explicit owner and file boundaries."""

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime

from ..profile import ProfileError, fields, label, require

OWNERS = frozenset(("runtime", "planning", "artifact", "research", "knowledge", "registry"))
ROLES = frozenset(("postgres", "qdrant", "artifact", "installation", "cut_evidence"))
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}


def digest(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), "backup_digest")
    return value


def identifier(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{32}", value), "backup_identity")
    return value


def relative_path(value):
    require(type(value) is str and 0 < len(value) <= 240, "backup_path")
    for part in value.split("/"):
        require(re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}", part)
                and not part.endswith(".") and part.split(".")[0].lower() not in RESERVED, "backup_path")
    require(value.lower() != "manifest.json", "backup_reserved_path")
    return value


@dataclass(frozen=True)
class SnapshotFile:
    path: str
    role: str
    size: int
    sha256: str

    @classmethod
    def parse(cls, value):
        v = fields(value, "path role size sha256", "backup_file")
        relative_path(v["path"])
        require(type(v["role"]) is str and v["role"] in ROLES, "backup_file_role")
        require(type(v["size"]) is int and 0 <= v["size"] <= 2**53 - 1, "backup_file_size")
        digest(v["sha256"])
        return cls(**v)


@dataclass(frozen=True)
class OwnerSnapshot:
    owner: str
    release: str
    schema: str
    checkpoint_sha256: str

    @classmethod
    def parse(cls, value):
        v = fields(value, "owner release schema checkpoint_sha256", "backup_owner")
        require(type(v["owner"]) is str and v["owner"] in OWNERS, "backup_owner_name")
        label(v["release"], "backup_owner_release")
        label(v["schema"], "backup_owner_schema")
        digest(v["checkpoint_sha256"])
        return cls(**v)


@dataclass(frozen=True)
class OfflineCut:
    mode: str
    evidence_path: str

    @classmethod
    def parse(cls, value):
        v = fields(value, "mode evidence_path", "backup_cut")
        require(v["mode"] == "all_owners_stopped", "backup_cut_mode")
        return cls(v["mode"], relative_path(v["evidence_path"]))


@dataclass(frozen=True)
class BackupManifest:
    profile: str
    backup_id: str
    source_deployment_id: str
    captured_at: str
    cut: OfflineCut
    owners: tuple[OwnerSnapshot, ...]
    files: tuple[SnapshotFile, ...]

    @classmethod
    def from_bytes(cls, raw):
        require(type(raw) is bytes and 0 < len(raw) <= 8 * 1024 * 1024, "backup_manifest_bytes")

        def unique(pairs):
            result = {}
            for key, value in pairs:
                require(key not in result, "backup_duplicate_key")
                result[key] = value
            return result

        try:
            record = json.loads(raw, object_pairs_hook=unique)
        except (ValueError, UnicodeDecodeError, RecursionError) as error:
            if isinstance(error, ProfileError):
                raise
            raise ProfileError("backup_manifest_json") from None
        v = fields(record, "profile backup_id source_deployment_id captured_at cut owners files", "backup_manifest")
        require(v["profile"] == "local-offline-backup-v1", "backup_profile")
        identifier(v["backup_id"])
        identifier(v["source_deployment_id"])
        require(type(v["captured_at"]) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v["captured_at"]), "backup_timestamp")
        try:
            datetime.strptime(v["captured_at"], "%Y-%m-%d %H:%M:%S")  # noqa: DTZ007 - validates declared local text only
        except ValueError:
            raise ProfileError("backup_timestamp") from None
        require(type(v["owners"]) is list and len(v["owners"]) == len(OWNERS), "backup_owners")
        owners = tuple(OwnerSnapshot.parse(row) for row in v["owners"])
        require({row.owner for row in owners} == OWNERS, "backup_owner_set")
        require(type(v["files"]) is list and 4 <= len(v["files"]) <= 10000, "backup_files")
        files = tuple(SnapshotFile.parse(row) for row in v["files"])
        paths = {row.path.casefold() for row in files}
        require(len(paths) == len(files), "backup_duplicate_path")
        require(not any('/'.join(row.path.casefold().split('/')[:i]) in paths
                        for row in files for i in range(1, len(row.path.split('/')))), "backup_path_conflict")
        for role in ("postgres", "qdrant", "cut_evidence"):
            require(sum(row.role == role for row in files) == 1, "backup_required_file")
        require(any(row.role == "installation" for row in files), "backup_installation_missing")
        cut = OfflineCut.parse(v["cut"])
        require(any(row.path == cut.evidence_path and row.role == "cut_evidence" for row in files), "backup_cut_reference")
        return cls(v["profile"], v["backup_id"], v["source_deployment_id"], v["captured_at"], cut, owners, files)

    def canonical_bytes(self):
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

    def require_compatible(self, expected_owners):
        actual = {row.owner: (row.release, row.schema) for row in self.owners}
        require(actual == expected_owners, "backup_owner_incompatible")

    def require_separate_target(self, target_deployment_id):
        identifier(target_deployment_id)
        require(target_deployment_id != self.source_deployment_id, "backup_target_is_source")
