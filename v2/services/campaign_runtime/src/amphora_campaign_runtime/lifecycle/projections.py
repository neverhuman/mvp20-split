"""Explicit mapping from owned claim context to public worker DTOs."""

from dataclasses import dataclass
from datetime import UTC

from amphora_contracts_core import Scope
from amphora_contracts_runtime import ClaimResponse, PreparedInvocation
from amphora_contracts_tools import Invocation

from .model import AttemptLease


@dataclass(frozen=True, slots=True)
class ClaimedWork:
    prepared: PreparedInvocation
    lease: AttemptLease
    scope: Scope
    run_id: str

    def to_response(self, reply, revision):
        prepared, lease = self.prepared, self.lease
        invocation = Invocation(schema_version="1", scope=self.scope, run_id=self.run_id,
            node_id=prepared.node_id, activation_id=prepared.activation_id, invocation_id=prepared.invocation_id,
            attempt_id=lease.attempt_id, fence=lease.fence, tool=prepared.tool, inputs=prepared.inputs,
            checkpoint=prepared.checkpoint, timeout_seconds=prepared.timeout_seconds, grant_id=lease.attempt_id)
        receipt = reply.accepted("attempt", lease.attempt_id, revision)
        return ClaimResponse.model_validate({"outcome": {"status": "claimed", "receipt": receipt.outcome.model_dump(),
            "invocation": invocation.model_dump(), "lease_expires_at": lease.expires_at.astimezone(UTC).isoformat().replace("+00:00", "Z")}})
