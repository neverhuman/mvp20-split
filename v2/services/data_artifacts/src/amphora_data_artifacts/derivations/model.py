"""Immutable declaration identity and input-set semantics, without SQL or I/O."""

import json
from dataclasses import dataclass

from amphora_contracts_artifacts import BeginDerivedUpload, DerivationReceipt, parse_command
from amphora_contracts_commands import CanonicalCommand

from ..publication.model import UploadError


@dataclass(frozen=True, slots=True)
class DeclaredTransformation:
    command: CanonicalCommand
    request: BeginDerivedUpload

    @classmethod
    def authorized(cls, principal, command):
        principal.require("upload", command.identity)
        principal.require("read")
        # Do not trust a manually constructed CanonicalCommand's identity or bytes.
        validated = parse_command("artifacts.begin_derived_upload", command.canonical_bytes)
        if validated != command:
            raise UploadError("derivation_command_mismatch")
        request = BeginDerivedUpload.model_validate_json(json.dumps(json.loads(validated.canonical_bytes)["payload"]))
        identities = [ref.artifact_id for ref in request.declaration.inputs]
        if len(set(identities)) != len(identities):
            raise UploadError("derivation_duplicate_input")
        return cls(validated, request)

    @property
    def input_ids(self):
        return tuple(ref.artifact_id for ref in self.request.declaration.inputs)

    def receipt(self, upload_id, artifact):
        if artifact.scope != self.command.identity.scope:
            raise UploadError("derivation_scope_mismatch")
        content = self.request.content
        if (artifact.sha256, artifact.size_bytes, artifact.media_type, artifact.schema_ref) != (
            content.sha256, content.size_bytes, content.media_type, content.schema_ref
        ):
            raise UploadError("derivation_output_mismatch")
        return DerivationReceipt(origin=self.command.identity, request_sha256=self.command.sha256,
                                 upload_id=upload_id, artifact=artifact, declaration=self.request.declaration)
