"""Typed client projections reject mismatched grants, artifacts and receipts."""

import hashlib
import json

import pytest
from amphora_contracts_artifacts import ContentDescriptor, UploadReceipt
from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_runtime import AttemptRef, CompleteInvocation
from amphora_contracts_tools import Completion, ToolBinding
from amphora_tool_protocol import (
    ArtifactClient,
    CommandRejected,
    ProtocolError,
    Reply,
    RuntimeClient,
    WorkerIdentity,
)

IDENTITY = WorkerIdentity("worker", Scope(tenant_id="test", project_id="clients"))
TOOL = ToolBinding(capability_id="synthetic.tool", release="0.2.0", image_sha256="a" * 64, contract_version="1")
CONTENT = ContentDescriptor.model_validate_json(json.dumps({"sha256": hashlib.sha256(b"data").hexdigest(),
    "size_bytes": 4, "media_type": "application/json", "schema_ref": {"schema_id": "payload", "version": "1", "sha256": "b" * 64}}))
UPLOAD = UploadReceipt(upload_id="upload", scope=IDENTITY.scope, content=CONTENT)
REFERENCE = ArtifactRef(artifact_id="artifact", scope=IDENTITY.scope, **CONTENT.model_dump())


def reply(value, status=200):
    return Reply(status, json.dumps(value).encode())


class Peer:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def request(self, method, path, body=None, **_kwargs):
        self.calls.append((method, path, body))
        value = next(self.replies)
        return value(body) if callable(value) else value


def accepted(body, kind="attempt", object_id="attempt"):
    return {"status": "accepted", "binding": {"identity": json.loads(body)["identity"],
        "request_sha256": hashlib.sha256(body).hexdigest(), "operation_id": "operation"},
        "committed": {"kind": kind, "object_id": object_id, "revision": 1}}


def claim(body):
    return {"outcome": {"status": "claimed", "receipt": accepted(body),
        "lease_expires_at": "2026-09-28T20:00:00Z", "invocation": {"schema_version": "1",
            "scope": IDENTITY.scope.model_dump(), "run_id": "run", "node_id": "node",
            "activation_id": "activation", "invocation_id": "invocation", "attempt_id": "attempt",
            "fence": 1, "tool": TOOL.model_dump(), "inputs": [{"port": "input", "artifact": REFERENCE.model_dump()}],
            "timeout_seconds": 60, "grant_id": "grant"}}}


def test_claim_no_work_rejection_and_malformed_owner_results():
    peer = Peer([lambda body: reply(claim(body)), lambda body: reply({"outcome": {
        "status": "no_eligible_work", "receipt": accepted(body, "run", "run")}})])
    client = RuntimeClient(peer, IDENTITY)
    assert client.claim("run", TOOL, "claim").outcome.invocation.tool == TOOL
    assert client.claim("run", TOOL, "empty").outcome.status == "no_eligible_work"
    def rejected(body):
        outcome = accepted(body)
        del outcome["committed"]
        return reply({"outcome": {**outcome, "status": "rejected", "reason_code": "worker_revoked"}})
    with pytest.raises(CommandRejected, match="worker_revoked"):
        RuntimeClient(Peer([rejected]), IDENTITY).claim("run", TOOL, "rejected")
    with pytest.raises(ProtocolError, match="invalid_owner_response"):
        RuntimeClient(Peer([Reply(200, b"private malformed diagnostic")]), IDENTITY).claim("run", TOOL, "bad")
    with pytest.raises(ProtocolError, match="invalid_claim_response"):
        RuntimeClient(Peer([lambda body: reply({"outcome": accepted(body)})]), IDENTITY).claim("run", TOOL, "bad")


@pytest.mark.parametrize("change", ["tool", "scope", "run", "input", "checkpoint", "receipt"])
def test_claim_rejects_every_foreign_binding(change):
    def changed(body):
        value = claim(body)
        invocation = value["outcome"]["invocation"]
        if change == "tool":
            invocation["tool"]["image_sha256"] = "f" * 64
        elif change == "scope":
            invocation["scope"]["project_id"] = "other"
        elif change == "run":
            invocation["run_id"] = "other"
        elif change == "input":
            invocation["inputs"][0]["artifact"]["scope"]["project_id"] = "other"
        elif change == "checkpoint":
            invocation["checkpoint"] = {**REFERENCE.model_dump(), "scope": {"tenant_id": "other", "project_id": "other"}}
        else:
            value["outcome"]["receipt"]["committed"]["object_id"] = "other"
        return reply(value)
    with pytest.raises(ProtocolError, match="claim_binding_mismatch"):
        RuntimeClient(Peer([changed]), IDENTITY).claim("run", TOOL, "claim")


def test_completion_requires_same_scope_and_completion_receipt():
    failed = Completion.model_validate_json(json.dumps({"schema_version": "1", "invocation_id": "invocation",
        "attempt_id": "attempt", "fence": 1, "outcome": {"status": "failed", "reason_code": "invalid_input", "retryable": False}}))
    request = CompleteInvocation(run_id="run", completion=failed)
    client = RuntimeClient(Peer([lambda body: reply({"outcome": accepted(body, "completion", "result")})]), IDENTITY)
    assert client.complete(request, "complete").outcome.status == "accepted"
    with pytest.raises(ProtocolError, match="invalid_completion_request"):
        client.complete(failed, "wrong")
    with pytest.raises(ProtocolError, match="completion_receipt_mismatch"):
        RuntimeClient(Peer([lambda body: reply({"outcome": accepted(body)})]), IDENTITY).complete(request, "bad")
    foreign = {**REFERENCE.model_dump(), "scope": {"tenant_id": "other", "project_id": "other"}}
    succeeded = failed.model_dump()
    succeeded["outcome"] = {"status": "succeeded", "outputs": [{"port": "result", "artifact": foreign}]}
    request = CompleteInvocation.model_validate_json(json.dumps({"run_id": "run", "completion": succeeded}))
    peer = Peer([])
    with pytest.raises(ValueError, match="scope_mismatch"):
        RuntimeClient(peer, IDENTITY).complete(request, "foreign")
    assert peer.calls == []


def test_run_snapshot_binding():
    value = {"scope": IDENTITY.scope.model_dump(), "run_id": "run", "fixture_id": "fixture", "plan_sha256": "a" * 64,
             "status": "running", "revision": 1, "budget": {"limit": 1, "available": 1, "reserved": 0, "spent": 0},
             "activations": []}
    assert RuntimeClient(Peer([reply(value)]), IDENTITY).run("run").run_id == "run"
    with pytest.raises(ProtocolError, match="run_binding_mismatch"):
        RuntimeClient(Peer([reply({**value, "run_id": "other"})]), IDENTITY).run("run")
    with pytest.raises(ProtocolError, match="run_unavailable"):
        RuntimeClient(Peer([reply({}, 404)]), IDENTITY).run("run")


def test_artifact_stream_finalize_and_verified_read():
    final = {"upload_id": "upload", "artifact": REFERENCE.model_dump()}
    peer = Peer([reply({"upload_id": "upload", "attempt_id": "stream", "generation": 1}), reply(final),
                 reply(REFERENCE.model_dump()), Reply(200, b"data")])
    client = ArtifactClient(peer, IDENTITY)
    assert client.stream(UPLOAD, b"data").status == "streamed"
    assert client.finalize(UPLOAD, "final").artifact == REFERENCE
    assert client.read(REFERENCE) == b"data"
    assert [method for method, _, _ in peer.calls] == ["PUT", "POST", "GET", "GET"]


@pytest.mark.parametrize("change", ["upload", "scope", "digest", "size", "schema", "media"])
def test_finalization_rejects_mismatched_reference(change):
    value = {"upload_id": "upload", "artifact": REFERENCE.model_dump()}
    if change == "upload":
        value["upload_id"] = "other"
    elif change == "scope":
        value["artifact"]["scope"]["project_id"] = "other"
    elif change == "digest":
        value["artifact"]["sha256"] = "f" * 64
    elif change == "size":
        value["artifact"]["size_bytes"] = 3
    elif change == "schema":
        value["artifact"]["schema_ref"]["schema_id"] = "other"
    else:
        value["artifact"]["media_type"] = "text/plain"
    with pytest.raises(ProtocolError, match="finalization_receipt_mismatch"):
        ArtifactClient(Peer([reply(value)]), IDENTITY).finalize(UPLOAD, "final")


def test_artifact_input_stream_and_download_fail_closed():
    peer = Peer([])
    client = ArtifactClient(peer, IDENTITY)
    with pytest.raises(ProtocolError, match="upload_content_mismatch"):
        client.stream(UPLOAD, b"oops")
    foreign = REFERENCE.model_copy(update={"scope": Scope(tenant_id="other", project_id="other")})
    with pytest.raises(ProtocolError, match="artifact_reference_denied"):
        client.read(foreign)
    with pytest.raises(ProtocolError, match="upload_scope_mismatch"):
        client.finalize(UPLOAD.model_copy(update={"scope": foreign.scope}), "final")
    assert peer.calls == []
    with pytest.raises(ProtocolError, match="stream_unavailable"):
        ArtifactClient(Peer([Reply(503, b"")]), IDENTITY).stream(UPLOAD, b"data")
    with pytest.raises(ProtocolError, match="stream_receipt_mismatch"):
        ArtifactClient(Peer([reply({"upload_id": "other", "attempt_id": "stream", "generation": 1})]), IDENTITY).stream(UPLOAD, b"data")
    with pytest.raises(ProtocolError, match="artifact_reference_mismatch"):
        ArtifactClient(Peer([reply(foreign.model_dump())]), IDENTITY).read(REFERENCE)
    with pytest.raises(ProtocolError, match="artifact_integrity_mismatch"):
        ArtifactClient(Peer([reply(REFERENCE.model_dump()), Reply(200, b"oops")]), IDENTITY).read(REFERENCE)


def test_renewal_and_upload_receipts_cannot_substitute_other_objects():
    attempt = AttemptRef(run_id="run", invocation_id="invocation", attempt_id="attempt", fence=1)
    with pytest.raises(ProtocolError, match="renewal_binding_mismatch"):
        RuntimeClient(Peer([lambda body: reply({"outcome": accepted(body, object_id="other")})]), IDENTITY).renew(attempt, "renew")
    changed = UPLOAD.model_dump()
    changed["content"]["sha256"] = "f" * 64
    with pytest.raises(ProtocolError, match="upload_receipt_mismatch"):
        ArtifactClient(Peer([reply(changed)]), IDENTITY).begin(CONTENT, "upload")
