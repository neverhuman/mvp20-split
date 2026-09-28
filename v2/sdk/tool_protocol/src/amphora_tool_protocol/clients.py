"""Worker-only public clients; no admission, cancellation, SQL or scientific policy."""

import hashlib

from amphora_contracts_artifacts import (
    BeginUpload,
    FinalizeArtifact,
    FinalizedReceipt,
    PublicationObservation,
    UploadContentReceipt,
    UploadReceipt,
)
from amphora_contracts_core import ArtifactRef
from amphora_contracts_runtime import (
    ClaimInvocation,
    ClaimResponse,
    CompleteInvocation,
    RenewAttempt,
    RunSnapshot,
    parse_command,
)

from .commands import (
    CommandExchange,
    decoded,
    publication_result,
    runtime_result,
)
from .transport import ProtocolError


class RuntimeClient:
    def __init__(self, transport, identity):
        self.transport, self.identity = transport, identity
        self.exchange = CommandExchange(transport)

    def claim(self, run_id, tool, command_id, *, lease_seconds=30):
        payload = ClaimInvocation(run_id=run_id, worker_id=self.identity.actor_id, tool=tool, lease_seconds=lease_seconds)
        command = self.identity.command("runtime.claim", command_id, payload)
        result = self.exchange.execute(command, "/v1/invocations/claim", runtime_result, runtime_result)
        if not isinstance(result, ClaimResponse):
            raise ProtocolError("invalid_claim_response")
        if result.outcome.status == "claimed":
            invocation = result.outcome.invocation
            if (invocation.scope != self.identity.scope or invocation.run_id != run_id or invocation.tool != tool
                or any(binding.artifact.scope != self.identity.scope for binding in invocation.inputs)
                or (invocation.checkpoint is not None and invocation.checkpoint.scope != self.identity.scope)
                or result.outcome.receipt.committed.kind != "attempt"
                or result.outcome.receipt.committed.object_id != invocation.attempt_id):
                raise ProtocolError("claim_binding_mismatch")
        return result

    def renew(self, attempt, command_id, *, lease_seconds=30, guard=lambda: None):
        command = self.identity.command("runtime.renew", command_id,
            RenewAttempt(attempt=attempt, lease_seconds=lease_seconds))
        result = self.exchange.execute(command, "/v1/attempts/renew", runtime_result, runtime_result, guard=guard)
        if (isinstance(result, ClaimResponse) or result.outcome.status != "accepted"
            or result.outcome.committed.kind != "attempt" or result.outcome.committed.object_id != attempt.attempt_id):
            raise ProtocolError("renewal_binding_mismatch")
        return result

    def complete(self, completion, command_id, *, guard=lambda: None):
        if not isinstance(completion, CompleteInvocation):
            raise ProtocolError("invalid_completion_request")
        command = self.identity.command("runtime.complete", command_id, completion)
        command = parse_command("runtime.complete", command.canonical_bytes)
        result = self.exchange.execute(command, "/v1/invocations/complete", runtime_result, runtime_result, guard=guard)
        if (isinstance(result, ClaimResponse) or result.outcome.status != "accepted"
            or result.outcome.committed.kind != "completion"):
            raise ProtocolError("completion_receipt_mismatch")
        return result

    def run(self, run_id):
        reply = self.transport.request("GET", f"/v1/runs/{run_id}")
        if reply.status != 200:
            raise ProtocolError("run_unavailable")
        result = decoded(RunSnapshot, reply.body)
        if result.scope != self.identity.scope or result.run_id != run_id:
            raise ProtocolError("run_binding_mismatch")
        return result


class ArtifactClient:
    def __init__(self, transport, identity):
        self.transport, self.identity = transport, identity
        self.exchange = CommandExchange(transport)

    def begin(self, content, command_id, *, guard=lambda: None):
        command = self.identity.command("artifacts.begin_upload", command_id, BeginUpload(content=content))
        result = self.exchange.execute(command, "/v1/uploads", lambda _cmd, body: decoded(UploadReceipt, body),
                                       publication_result, guard=guard)
        if isinstance(result, PublicationObservation):
            if result.outcome.status != "uploaded":
                raise ProtocolError("upload_receipt_mismatch")
            result = result.outcome.receipt
        if result.scope != self.identity.scope or result.content != content:
            raise ProtocolError("upload_receipt_mismatch")
        return result

    def stream(self, upload, payload, *, guard=lambda: None):
        if (upload.scope != self.identity.scope or len(payload) > 16 * 1024 * 1024 or len(payload) != upload.content.size_bytes
            or hashlib.sha256(payload).hexdigest() != upload.content.sha256):
            raise ProtocolError("upload_content_mismatch")
        guard()
        # Streaming has no command identity. Never automatically retry an ambiguous PUT.
        reply = self.transport.request("PUT", f"/v1/uploads/{upload.upload_id}/content", payload,
                                       media_type=upload.content.media_type)
        if reply.status != 200:
            raise ProtocolError("stream_unavailable")
        result = decoded(UploadContentReceipt, reply.body)
        if result.upload_id != upload.upload_id:
            raise ProtocolError("stream_receipt_mismatch")
        return result

    def finalize(self, upload, command_id, *, guard=lambda: None):
        if upload.scope != self.identity.scope:
            raise ProtocolError("upload_scope_mismatch")
        command = self.identity.command("artifacts.finalize", command_id,
            FinalizeArtifact(upload_id=upload.upload_id, content=upload.content))
        result = self.exchange.execute(command, "/v1/artifacts/finalize", lambda _cmd, body: decoded(FinalizedReceipt, body),
                                       publication_result, guard=guard)
        if isinstance(result, PublicationObservation):
            if result.outcome.status != "finalized":
                raise ProtocolError("finalization_receipt_mismatch")
            result = result.outcome.receipt
        reference = result.artifact
        if (result.upload_id != upload.upload_id or reference.scope != self.identity.scope
            or reference.sha256 != upload.content.sha256 or reference.size_bytes != upload.content.size_bytes
            or reference.media_type != upload.content.media_type or reference.schema_ref != upload.content.schema_ref):
            raise ProtocolError("finalization_receipt_mismatch")
        return result

    def read(self, reference: ArtifactRef):
        if reference.scope != self.identity.scope or reference.size_bytes > 16 * 1024 * 1024:
            raise ProtocolError("artifact_reference_denied")
        path = f"/v1/artifacts/{reference.artifact_id}"
        metadata = self.transport.request("GET", path)
        if metadata.status != 200 or decoded(ArtifactRef, metadata.body) != reference:
            raise ProtocolError("artifact_reference_mismatch")
        reply = self.transport.request("GET", path + "/content", limit=reference.size_bytes)
        if (reply.status != 200 or len(reply.body) != reference.size_bytes
            or hashlib.sha256(reply.body).hexdigest() != reference.sha256):
            raise ProtocolError("artifact_integrity_mismatch")
        return reply.body
