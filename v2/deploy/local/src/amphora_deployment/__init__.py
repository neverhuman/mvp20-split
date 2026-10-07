"""Local deployment configuration; no installation or service-state authority."""

from .profile import DeploymentProfile, ProfileError

__all__ = ["DeploymentProfile", "ProfileError"]
