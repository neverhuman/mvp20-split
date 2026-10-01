"""Bounded synthetic/local rights policy and replay-fence values."""

from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_evidence import RightsRevisionRef, SourceRightsRevision

from ..publication.model import UploadError


class RightsError(UploadError):
    """Safe policy reason; no source content or credentials."""


@dataclass(frozen=True)
class RightsPolicy:
    record: SourceRightsRevision

    def __post_init__(self):
        record = self.record
        prior = record.supersedes
        ref = record.reference
        if ((prior is None and ref.revision != 1) or (prior is not None and
            (prior.scope != ref.scope or prior.rights_id != ref.rights_id or prior.revision + 1 != ref.revision))):
            raise RightsError("rights_invalid_predecessor")
        if len(set(record.allowed_uses)) != len(record.allowed_uses):
            raise RightsError("rights_duplicate_use")
        if (record.status == "revoked") != (len(record.allowed_uses) == 0):
            raise RightsError("rights_invalid_grant")
        if "process" in record.allowed_uses and "read" not in record.allowed_uses:
            raise RightsError("rights_process_requires_read")

    def require(self, use, now):
        if self.record.status == "revoked":
            raise RightsError("rights_revoked")
        if self.record.expires_at is not None and now >= self.record.expires_at:
            raise RightsError("rights_expired")
        if use not in self.record.allowed_uses:
            raise RightsError("rights_use_denied")


@dataclass(frozen=True)
class RightsSnapshot:
    scope: Scope
    artifacts: tuple[str, ...]
    declared: tuple[RightsRevisionRef, ...]
    use: str
    heads: tuple[tuple[str, int], ...]
