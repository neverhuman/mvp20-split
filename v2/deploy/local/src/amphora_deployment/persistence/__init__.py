"""Explicitly owned local data-store provisioning; retains all data on failure."""

from .stores import ensure_local_stores

__all__ = ["ensure_local_stores"]
