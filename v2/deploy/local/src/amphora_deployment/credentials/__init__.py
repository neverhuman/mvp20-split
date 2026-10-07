"""Current-user protected local credentials; values never enter installation records."""

from .vault import CredentialVault, SecretBundle

__all__ = ["CredentialVault", "SecretBundle"]
