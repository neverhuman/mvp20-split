"""Scoped bounded inspection DTOs; historical observations are never grants."""

from typing import Annotated, Literal

from amphora_contracts_core import Identifier, Scope, WireModel
from amphora_contracts_tools import Completion
from pydantic import Field

from .models import Revision, UtcTimestamp

Cursor = Annotated[str, Field(min_length=1, max_length=4096)]


class AuditEntry(WireModel):
    event_id: Identifier
    revision: Revision
    ordinal: Revision
    event_kind: Identifier


class AuditPage(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    run_id: Identifier
    snapshot_revision: Revision
    entries: Annotated[tuple[AuditEntry, ...], Field(max_length=100)]
    next_cursor: Cursor | None


class DeliverySnapshot(WireModel):
    operation_id: Identifier
    event_id: Identifier
    target: Identifier
    status: Literal["pending", "leased", "acknowledged", "exhausted"]
    attempts: Revision
    generation: Revision
    available_at: UtcTimestamp
    lease_expires_at: UtcTimestamp | None
    last_reason: Identifier | None


class DeliveryPage(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    journal: Literal["run", "policy"]
    event_id: Identifier
    entries: Annotated[tuple[DeliverySnapshot, ...], Field(max_length=100)]
    next_cursor: Cursor | None


class CompletionRecord(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    run_id: Identifier
    completion_id: Identifier
    activation_id: Identifier
    accepted_run_revision: Revision
    canonical_result: bool
    retention_reservation_ids: Annotated[tuple[Identifier, ...], Field(max_length=65)] = ()
    result: Completion
