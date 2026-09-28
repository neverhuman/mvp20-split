"""Durable-runtime wire shapes, not live lease/authority/transition policies."""

from typing import Annotated, Literal

from amphora_contracts_commands import CommandIdentity
from amphora_contracts_core import ArtifactRef, Digest, Identifier, SafePositiveInt, WireModel
from amphora_contracts_tools import Completion, InputBinding, Invocation, ToolBinding
from pydantic import Field

Revision = Annotated[int, Field(ge=0, le=9007199254740991)]
LeaseSeconds = Annotated[int, Field(ge=1, le=300)]
UtcTimestamp = Annotated[str, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T([01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,6})?Z$")]


class PreparedInvocation(WireModel):
    node_id: Identifier
    activation_id: Identifier
    invocation_id: Identifier
    tool: ToolBinding
    inputs: Annotated[tuple[InputBinding, ...], Field(max_length=64)]
    checkpoint: ArtifactRef | None = None
    timeout_seconds: Annotated[int, Field(ge=1, le=86400)]
    side_effects: Literal["pure"] = "pure"


class AttemptBudget(WireModel):
    limit: SafePositiveInt
    max_attempts_per_activation: Annotated[int, Field(ge=1, le=100)] = 3


class AdmitFixtureRun(WireModel):
    fixture_id: Identifier
    plan_sha256: Digest
    invocations: Annotated[tuple[PreparedInvocation, ...], Field(min_length=1, max_length=256)]
    budget: AttemptBudget


class ClaimInvocation(WireModel):
    run_id: Identifier
    worker_id: Identifier
    tool: ToolBinding
    lease_seconds: LeaseSeconds = 30


class AttemptRef(WireModel):
    run_id: Identifier
    invocation_id: Identifier
    attempt_id: Identifier
    fence: SafePositiveInt


class RenewAttempt(WireModel):
    attempt: AttemptRef
    lease_seconds: LeaseSeconds = 30


class CompleteInvocation(WireModel):
    run_id: Identifier
    completion: Completion
    expected_checkpoint_revision: Revision | None = None


class CancelRun(WireModel):
    run_id: Identifier
    expected_run_revision: Revision | None = None
    reason_code: Identifier


class RevokeWorker(WireModel):
    worker_id: Identifier
    reason_code: Identifier


class ReceiptBinding(WireModel):
    identity: CommandIdentity
    request_sha256: Digest
    operation_id: Identifier


class PendingReceipt(WireModel):
    status: Literal["pending"]
    binding: ReceiptBinding


class CommittedReference(WireModel):
    kind: Literal["run", "attempt", "completion", "worker_policy"]
    object_id: Identifier
    revision: Revision


class AcceptedReceipt(WireModel):
    status: Literal["accepted"]
    binding: ReceiptBinding
    committed: CommittedReference


class RejectedReceipt(WireModel):
    status: Literal["rejected"]
    binding: ReceiptBinding
    reason_code: Identifier


class CommandReceipt(WireModel):
    schema_version: Literal["1"] = "1"
    outcome: Annotated[PendingReceipt | AcceptedReceipt | RejectedReceipt, Field(discriminator="status")]


class ClaimedInvocation(WireModel):
    status: Literal["claimed"]
    receipt: AcceptedReceipt
    invocation: Invocation
    lease_expires_at: UtcTimestamp


class NoEligibleWork(WireModel):
    status: Literal["no_eligible_work"]
    receipt: AcceptedReceipt


class ClaimResponse(WireModel):
    schema_version: Literal["1"] = "1"
    outcome: Annotated[ClaimedInvocation | NoEligibleWork, Field(discriminator="status")]
