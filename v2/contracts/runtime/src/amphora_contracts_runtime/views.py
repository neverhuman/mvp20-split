"""Bounded inspection snapshots; observations never authorize worker actions."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, Scope, WireModel
from pydantic import Field

from .models import Revision, UtcTimestamp


class BudgetView(WireModel):
    limit: Revision
    available: Revision
    reserved: Revision
    spent: Revision


class AttemptView(WireModel):
    attempt_id: Identifier
    worker_id: Identifier
    fence: Revision
    status: Literal["leased", "succeeded", "abstained", "failed", "expired", "cancelled", "uncertain"]
    lease_expires_at: UtcTimestamp
    deadline: UtcTimestamp


class ActivationView(WireModel):
    activation_id: Identifier
    invocation_id: Identifier
    status: Literal["queued", "leased", "succeeded", "abstained", "failed", "cancelled", "uncertain"]
    fence: Revision
    attempt_count: Revision
    latest_attempt: AttemptView | None


class RunSnapshot(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    run_id: Identifier
    fixture_id: Identifier
    plan_sha256: Digest
    status: Literal["running", "completed", "cancelled", "failed", "blocked"]
    revision: Revision
    budget: BudgetView
    activations: Annotated[tuple[ActivationView, ...], Field(max_length=256)]
