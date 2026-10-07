"""Read-only file verification against a separately retained manifest digest."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..profile import ProfileError, require
from .manifest import BackupManifest, digest


def plain_path(root, relative):
    path = root
    require(not root.is_symlink() and not root.is_junction(), "backup_link")
    for part in relative.split('/'):
        path = path / part
        require(not path.is_symlink() and not path.is_junction(), "backup_link")
    return path


@dataclass(frozen=True)
class InventoryVerification:
    backup_id: str
    manifest_sha256: str
    file_count: int
    total_bytes: int
    status: str = "inventory_verified_not_restore_ready"


def verify_inventory(root, expected_manifest_sha256, expected_owners, target_deployment_id):
    """Caller owns exclusive offline access; does not defeat concurrent filesystem mutation."""
    digest(expected_manifest_sha256)
    root = Path(root).absolute()
    try:
        manifest_path = plain_path(root, 'manifest.json')
        with manifest_path.open('rb') as stream:
            raw = stream.read(8 * 1024 * 1024 + 1)
        require(hashlib.sha256(raw).hexdigest() == expected_manifest_sha256, "backup_manifest_digest")
        manifest = BackupManifest.from_bytes(raw)
        manifest.require_compatible(expected_owners)
        manifest.require_separate_target(target_deployment_id)
        total = 0
        for row in manifest.files:
            path = plain_path(root, row.path)
            require(path.is_file() and path.stat().st_size == row.size, "backup_file_missing_or_size")
            fingerprint, size = hashlib.sha256(), 0
            with path.open('rb') as stream:
                while block := stream.read(1024 * 1024):
                    fingerprint.update(block)
                    size += len(block)
            require(size == row.size and fingerprint.hexdigest() == row.sha256, "backup_file_digest")
            total += size
        return InventoryVerification(manifest.backup_id, expected_manifest_sha256, len(manifest.files), total)
    except OSError:
        raise ProfileError("backup_io") from None
