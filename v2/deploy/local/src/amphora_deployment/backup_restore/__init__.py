"""Offline backup inventory validation; never confers restored-service readiness."""

from .manifest import BackupManifest
from .verification import verify_inventory

__all__ = ["BackupManifest", "verify_inventory"]
