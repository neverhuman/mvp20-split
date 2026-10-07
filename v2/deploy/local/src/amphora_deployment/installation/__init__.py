"""Immutable owner inventory and explicit native-process launch recipes."""

from .inventory import InstallationInventory, OwnerInstallation
from .recipes import OWNERS

__all__ = ["InstallationInventory", "OwnerInstallation", "OWNERS"]
