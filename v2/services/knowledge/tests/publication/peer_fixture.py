"""Scripted Data HTTP boundary; not a substitute for actual-owner acceptance."""

import hashlib

from amphora_contracts_artifacts import (
    BeginDerivedUpload,
    DerivationReceipt,
    DerivedUploadObservation,
    DerivedUploadReceipt,
    FinalizeArtifact,
    FinalizedReceipt,
    PublicationObservation,
    UploadContentReceipt,
    UploadReceipt,
)
from amphora_contracts_commands import CanonicalCommand
from amphora_contracts_core import ArtifactRef
from amphora_tool_protocol import Reply, TransportLost


def reply(record):
    return Reply(200, record.model_dump_json().encode())


class PublicationPeer:
    def __init__(self):
        self.calls, self.commands, self.uploads, self.bytes, self.derivations = [], {}, {}, {}, {}
        self.drop_begin, self.drop_finalize, self.drop_stream = False, False, False
        self.deny_finalize = False
        self.before_request = lambda: None

    def request(self, method, path, body=None, **options):
        self.before_request()
        self.calls.append((method, path))
        if method == "GET" and path.startswith("/v1/commands/"):
            return reply(self.commands[path]) if path in self.commands else Reply(404, b'{}')
        if method == "POST":
            begin = path == "/v1/derived-uploads"
            model = BeginDerivedUpload if begin else FinalizeArtifact
            family = "artifacts.begin_derived_upload" if begin else "artifacts.finalize"
            command = CanonicalCommand.for_family(body, family, model)
            import json

            payload = model.model_validate_json(json.dumps(json.loads(body)["payload"]))
            key = f"/v1/commands/{family}/{command.identity.command_id}"
            if key in self.commands:
                assert self.commands[key].request_sha256 == command.sha256
                return reply(self.commands[key].outcome.receipt)
            if begin:
                upload = UploadReceipt(upload_id=f"upload-{len(self.uploads) + 1}", scope=command.identity.scope, content=payload.content)
                result = DerivedUploadReceipt(upload=upload, declaration=payload.declaration)
                observation = DerivedUploadObservation.model_validate({"identity": command.identity, "operation_id": "begin-op",
                    "request_sha256": command.sha256, "outcome": {"status": "derived_uploaded", "receipt": result}})
                self.uploads[upload.upload_id] = (result, command)
            else:
                original, begin_command = self.uploads[payload.upload_id]
                assert payload.content == original.upload.content
                assert hashlib.sha256(self.bytes[payload.upload_id]).hexdigest() == payload.content.sha256
                if self.deny_finalize:
                    self.commands[key] = PublicationObservation.model_validate({"identity": command.identity, "operation_id": "final-op",
                        "request_sha256": command.sha256, "outcome": {"status": "rejected", "reason_code": "rights_revoked"}})
                    return Reply(409, b'{}')
                ref = ArtifactRef(artifact_id="result-" + payload.upload_id, scope=command.identity.scope, **payload.content.model_dump())
                result = FinalizedReceipt(upload_id=payload.upload_id, artifact=ref)
                observation = PublicationObservation.model_validate({"identity": command.identity, "operation_id": "final-op",
                    "request_sha256": command.sha256, "outcome": {"status": "finalized", "receipt": result}})
                self.derivations[ref.artifact_id] = DerivationReceipt(origin=begin_command.identity, request_sha256=begin_command.sha256,
                    upload_id=payload.upload_id, artifact=ref, declaration=original.declaration)
            self.commands[key] = observation
            if begin and self.drop_begin:
                self.drop_begin = False
                raise TransportLost("lost_begin_ack")
            if not begin and self.drop_finalize:
                self.drop_finalize = False
                raise TransportLost("lost_finalize_ack")
            return reply(result)
        if method == "PUT":
            upload_id = path.split("/")[3]
            assert upload_id not in self.bytes, "an ambiguous PUT must never be repeated"
            self.bytes[upload_id] = body
            if self.drop_stream:
                self.drop_stream = False
                raise TransportLost("lost_stream_ack")
            return reply(UploadContentReceipt(upload_id=upload_id, attempt_id="stream-" + upload_id, generation=1))
        if method == "GET" and path.endswith("/derivation"):
            return reply(self.derivations[path.split("/")[3]])
        raise AssertionError((method, path))
