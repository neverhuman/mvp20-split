"""Scripted peers isolate client recovery; installed peer proof is a separate gate."""

import hashlib
import json

import pytest
from amphora_contracts_artifacts import ContentDescriptor, UploadReceipt
from amphora_contracts_core import Scope
from amphora_contracts_runtime import AttemptRef
from amphora_tool_protocol import (
    ArtifactClient,
    CommandRejected,
    CommandUnresolved,
    ProtocolError,
    Reply,
    RuntimeClient,
    TransportLost,
    WorkerIdentity,
)


class Scripted:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def request(self, method, path, body=None, **kwargs):
        self.calls.append((method, path, body))
        result = next(self.replies)
        if callable(result):
            result = result(self.calls)
        if isinstance(result, Exception):
            raise result
        return result


IDENTITY = WorkerIdentity("worker", Scope(tenant_id="fixture", project_id="sdk"))
CONTENT = ContentDescriptor.model_validate_json(json.dumps({"sha256": hashlib.sha256(b"data").hexdigest(),
    "size_bytes": 4, "media_type": "application/octet-stream", "schema_ref": {
        "schema_id": "fixture.bytes", "version": "1", "sha256": "a" * 64}}))
UPLOAD = UploadReceipt(upload_id="upload", scope=IDENTITY.scope, content=CONTENT)


def reply(value, status=200):
    return Reply(status, json.dumps(value).encode())


def observation(calls, outcome=None, *, identity_override=None, digest_override=None):
    body = next(body for method, _path, body in calls if method == "POST")
    raw = json.loads(body)
    return reply({"identity": identity_override or raw["identity"], "operation_id": "original-operation",
        "request_sha256": digest_override or hashlib.sha256(body).hexdigest(),
        "outcome": outcome or {"status": "uploaded", "receipt": UPLOAD.model_dump(mode="json")}})


def test_upload_ack_loss_recovers_without_second_post():
    transport = Scripted([TransportLost("transport_lost"), observation])
    assert ArtifactClient(transport, IDENTITY).begin(CONTENT, "original") == UPLOAD
    assert [method for method, _, _ in transport.calls] == ["POST", "GET"]
    assert transport.calls[1][1] == "/v1/commands/artifacts.begin_upload/original"


@pytest.mark.parametrize("lookup", [lambda _calls: reply({}, 404),
    lambda calls: observation(calls, {"status": "pending"})])
def test_uncommitted_request_retries_identical_bytes_after_lookup(lookup):
    transport = Scripted([Reply(503, b"unavailable"), lookup, reply(UPLOAD.model_dump(mode="json"))])
    assert ArtifactClient(transport, IDENTITY).begin(CONTENT, "original") == UPLOAD
    assert [method for method, _, _ in transport.calls] == ["POST", "GET", "POST"]
    assert transport.calls[0][2] == transport.calls[2][2]


def test_unavailable_lookup_never_blindly_resubmits():
    transport = Scripted([TransportLost("transport_lost"), Reply(503, b""), TransportLost("transport_lost")])
    with pytest.raises(CommandUnresolved) as error:
        ArtifactClient(transport, IDENTITY).begin(CONTENT, "original")
    assert error.value.identity.command_id == "original"
    assert [method for method, _, _ in transport.calls] == ["POST", "GET", "GET"]


@pytest.mark.parametrize("change", ["digest", "actor", "scope"])
def test_recovered_foreign_receipt_fails_closed(change):
    def foreign(calls):
        raw = json.loads(calls[0][2])["identity"]
        if change == "actor":
            raw["actor_id"] = "other"
        if change == "scope":
            raw["scope"]["project_id"] = "other"
        return observation(calls, identity_override=raw, digest_override="b" * 64 if change == "digest" else None)
    transport = Scripted([TransportLost("transport_lost"), foreign])
    with pytest.raises(ProtocolError, match="receipt_binding_mismatch"):
        ArtifactClient(transport, IDENTITY).begin(CONTENT, "original")


def test_persisted_rejection_and_stream_ambiguity_are_not_success():
    transport = Scripted([Reply(409, b"private diagnostics"),
        lambda calls: observation(calls, {"status": "rejected", "reason_code": "capacity_exhausted"})])
    with pytest.raises(CommandRejected, match="capacity_exhausted"):
        ArtifactClient(transport, IDENTITY).begin(CONTENT, "original")
    transport = Scripted([TransportLost("transport_lost")])
    with pytest.raises(TransportLost):
        ArtifactClient(transport, IDENTITY).stream(UPLOAD, b"data")
    assert len(transport.calls) == 1


def test_lost_authority_prevents_resubmit_but_not_original_receipt_read():
    guards = []
    def guard():
        guards.append(True)
        if len(guards) > 1:
            raise ProtocolError("authority_lost")
    transport = Scripted([TransportLost("transport_lost"), observation])
    assert ArtifactClient(transport, IDENTITY).begin(CONTENT, "original", guard=guard) == UPLOAD
    transport = Scripted([TransportLost("transport_lost"), Reply(404, b"")])
    guards.clear()
    with pytest.raises(ProtocolError, match="authority_lost"):
        ArtifactClient(transport, IDENTITY).begin(CONTENT, "original", guard=guard)
    assert len(transport.calls) == 2


def test_runtime_renewal_recovers_exact_accepted_binding():
    attempt = AttemptRef(run_id="run", invocation_id="invocation", attempt_id="attempt", fence=2)
    def receipt(calls):
        body = calls[0][2]
        return reply({"outcome": {"status": "accepted", "binding": {
            "identity": json.loads(body)["identity"], "request_sha256": hashlib.sha256(body).hexdigest(),
            "operation_id": "renew-operation"}, "committed": {"kind": "attempt", "object_id": "attempt", "revision": 3}}})
    transport = Scripted([TransportLost("transport_lost"), receipt])
    assert RuntimeClient(transport, IDENTITY).renew(attempt, "renew-1").outcome.status == "accepted"
    assert [method for method, _, _ in transport.calls] == ["POST", "GET"]
