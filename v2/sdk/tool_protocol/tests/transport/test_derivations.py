"""Scripted public peers isolate derived publication recovery and exact binding."""

import hashlib
import json

import pytest
from amphora_contracts_artifacts import (
    BeginDerivedUpload,
    ContentDescriptor,
    DerivationDeclaration,
    DerivedUploadReceipt,
    UploadReceipt,
)
from amphora_contracts_core import Scope
from amphora_tool_protocol import (
    ArtifactClient,
    CommandRejected,
    CommandUnresolved,
    ProtocolError,
    Reply,
    TransportLost,
    WorkerIdentity,
)

IDENTITY = WorkerIdentity("producer", Scope(tenant_id="test", project_id="derivations"))
CONTENT = ContentDescriptor.model_validate_json(json.dumps({"sha256": hashlib.sha256(b"data").hexdigest(),
    "size_bytes": 4, "media_type": "application/octet-stream",
    "schema_ref": {"schema_id": "bytes", "version": "1", "sha256": "b" * 64}}))
DECLARATION = DerivationDeclaration.model_validate_json(json.dumps({
    "transformation": {"transformation_id": "method", "version": "1", "sha256": "c" * 64},
    "inputs": [{"artifact_id": "input", "scope": IDENTITY.scope.model_dump(), **CONTENT.model_dump()}]}))
UPLOAD = UploadReceipt(upload_id="upload", scope=IDENTITY.scope, content=CONTENT)
RECEIPT = DerivedUploadReceipt(upload=UPLOAD, declaration=DECLARATION)
COMMAND = IDENTITY.command("artifacts.begin_derived_upload", "begin", BeginDerivedUpload(content=CONTENT, declaration=DECLARATION))


def reply(value, status=200):
    return Reply(status, json.dumps(value).encode())


def observation(outcome=None, **changes):
    return reply({"identity": COMMAND.identity.model_dump(), "operation_id": "op", "request_sha256": COMMAND.sha256,
                  "outcome": outcome or {"status": "derived_uploaded", "receipt": RECEIPT.model_dump(mode="json")}, **changes})


class Peer:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def request(self, method, path, body=None, **_kwargs):
        self.calls.append((method, path, body))
        value = next(self.replies)
        if isinstance(value, Exception):
            raise value
        return value


def test_ambiguous_derived_begin_recovers_original_receipt():
    peer = Peer([TransportLost("lost"), observation()])
    assert ArtifactClient(peer, IDENTITY).begin_derived(CONTENT, DECLARATION, "begin") == RECEIPT
    assert [method for method, _, _ in peer.calls] == ["POST", "GET"]
    assert peer.calls[0][2] == COMMAND.canonical_bytes


def test_process_restart_reconciles_before_any_write_or_guard():
    peer = Peer([observation()])
    def denied():
        raise AssertionError("Historical lookup must not invoke write guard")
    assert ArtifactClient(peer, IDENTITY).begin_derived(CONTENT, DECLARATION, "begin", resume=True, guard=denied) == RECEIPT
    assert [method for method, _, _ in peer.calls] == ["GET"]


@pytest.mark.parametrize("pending", [True, False])
def test_resume_known_pending_or_absent_preserves_exact_command(pending):
    peer = Peer([observation({"status": "pending"}) if pending else reply({}, 404), reply(RECEIPT.model_dump(mode="json"))])
    assert ArtifactClient(peer, IDENTITY).begin_derived(CONTENT, DECLARATION, "begin", resume=True) == RECEIPT
    assert [method for method, _, _ in peer.calls] == ["GET", "POST"]
    assert peer.calls[1][2] == COMMAND.canonical_bytes


def test_unavailable_original_receipt_never_reissues_begin():
    peer = Peer([Reply(503, b"")] * 3)
    with pytest.raises(CommandUnresolved) as error:
        ArtifactClient(peer, IDENTITY).begin_derived(CONTENT, DECLARATION, "begin", resume=True)
    assert error.value.request_sha256 == COMMAND.sha256
    assert [method for method, _, _ in peer.calls] == ["GET"] * 3


def test_rejected_and_foreign_original_receipts_are_terminal():
    peer = Peer([observation({"status": "rejected", "reason_code": "rights_revoked"})])
    with pytest.raises(CommandRejected, match="rights_revoked"):
        ArtifactClient(peer, IDENTITY).begin_derived(CONTENT, DECLARATION, "begin", resume=True)
    peer = Peer([observation(request_sha256="d" * 64)])
    with pytest.raises(ProtocolError, match="receipt_binding_mismatch"):
        ArtifactClient(peer, IDENTITY).begin_derived(CONTENT, DECLARATION, "begin", resume=True)


@pytest.mark.parametrize("field", ["scope", "content", "declaration"])
def test_success_must_match_scope_content_and_entire_declaration(field):
    raw = RECEIPT.model_dump(mode="json")
    if field == "scope":
        raw["upload"]["scope"]["project_id"] = "foreign"
    elif field == "content":
        raw["upload"]["content"]["sha256"] = "d" * 64
    else:
        raw["declaration"]["transformation"]["sha256"] = "d" * 64
    with pytest.raises(ProtocolError, match="derived_receipt_mismatch"):
        ArtifactClient(Peer([reply(raw)]), IDENTITY).begin_derived(CONTENT, DECLARATION, "begin")


def test_foreign_input_denied_before_network_and_uncertain_stream_is_not_retried():
    foreign = DECLARATION.model_copy(update={"inputs": (DECLARATION.inputs[0].model_copy(
        update={"scope": Scope(tenant_id="other", project_id="foreign")}),)})
    peer = Peer([])
    with pytest.raises(ProtocolError, match="derivation_scope_mismatch"):
        ArtifactClient(peer, IDENTITY).begin_derived(CONTENT, foreign, "begin")
    assert not peer.calls
    peer = Peer([TransportLost("lost")])
    with pytest.raises(TransportLost):
        ArtifactClient(peer, IDENTITY).stream(UPLOAD, b"data")
    assert [method for method, _, _ in peer.calls] == ["PUT"]


def test_finalize_resume_and_immutable_derivation_read():
    from amphora_contracts_artifacts import FinalizeArtifact
    from amphora_contracts_core import ArtifactRef
    artifact = ArtifactRef(artifact_id="output", scope=IDENTITY.scope, **CONTENT.model_dump())
    command = IDENTITY.command("artifacts.finalize", "final", FinalizeArtifact(upload_id="upload", content=CONTENT))
    outcome = {"status": "finalized", "receipt": {"upload_id": "upload", "artifact": artifact.model_dump(mode="json")}}
    metadata = {"origin": COMMAND.identity.model_dump(), "request_sha256": COMMAND.sha256,
                "upload_id": "upload", "artifact": artifact.model_dump(mode="json"), "declaration": DECLARATION.model_dump(mode="json")}
    peer = Peer([reply({"identity": command.identity.model_dump(), "operation_id": "op", "request_sha256": command.sha256,
                        "outcome": outcome}), reply(metadata)])
    client = ArtifactClient(peer, IDENTITY)
    assert client.finalize(UPLOAD, "final", resume=True).artifact == artifact
    assert client.derivation(artifact).origin == COMMAND.identity
    assert [method for method, _, _ in peer.calls] == ["GET", "GET"]
    metadata["origin"]["scope"]["project_id"] = "foreign"
    with pytest.raises(ProtocolError, match="derivation_reference_mismatch"):
        ArtifactClient(Peer([reply(metadata)]), IDENTITY).derivation(artifact)
