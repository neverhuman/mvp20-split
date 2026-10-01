"""Explicit current-use grants; immutable provenance retention is a separate policy."""

from typing import Annotated, Literal

from amphora_contracts_core import WireModel
from pydantic import AwareDatetime, Field

from .references import RightsRevisionRef


class SourceRightsRevision(WireModel):
    wire_version: Literal["1"]
    reference: RightsRevisionRef
    supersedes: RightsRevisionRef | None
    status: Literal["granted", "revoked"]
    allowed_uses: Annotated[tuple[Literal["read", "process"], ...], Field(max_length=2)]
    expires_at: AwareDatetime | None
    retention: Literal["retain_audit_payload"]
