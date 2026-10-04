"""One upload attempt; intent precedes I/O and uncertain PUT is never replayed."""

import hashlib
import json
from dataclasses import dataclass, replace

from amphora_contracts_artifacts import (
    BeginDerivedUpload,
    DerivationReceipt,
    DerivedUploadReceipt,
    FinalizeArtifact,
    FinalizedReceipt,
    UploadContentReceipt,
)
from amphora_contracts_commands import CanonicalCommand, CommandIdentity
from amphora_contracts_core import Identifier
from pydantic import TypeAdapter

from ..context.policy import require


@dataclass(frozen=True)
class AttemptIdentity:
    ordinal: int
    begin_id: str
    finalize_id: str

    @classmethod
    def for_publication(cls, identity, ordinal):
        require(type(ordinal) is int and 1 <= ordinal <= 8, "publication_attempt_limit")
        keys = [hashlib.sha256(f"{identity.sha256}:{ordinal}:{family}".encode()).hexdigest()
                for family in ("begin", "finalize")]
        return cls(ordinal, *keys)

    def command(self, identity, family, payload):
        require(family in {"artifacts.begin_derived_upload", "artifacts.finalize"}, "publication_command_family")
        key = self.begin_id if family == "artifacts.begin_derived_upload" else self.finalize_id
        command = CommandIdentity(command_family=family, command_id=key, actor_id=identity.actor_id,
                                   scope=identity.trace().scope)
        return CanonicalCommand.for_family(json.dumps({"identity": command.model_dump(mode="json"),
            "payload": payload.model_dump(mode="json")}), family, type(payload))


@dataclass(frozen=True)
class PublicationAttempt:
    identity: AttemptIdentity
    stage: str = "prepared"
    upload: DerivedUploadReceipt | None = None
    stream: UploadContentReceipt | None = None
    result: DerivationReceipt | None = None
    rejection: str | None = None

    @classmethod
    def first(cls, identity):
        return cls(AttemptIdentity.for_publication(identity, 1))

    def _at(self, stage):
        require(self.stage == stage, "publication_transition")

    def begin_command(self, identity, artifact):
        return self.identity.command(identity, "artifacts.begin_derived_upload",
            BeginDerivedUpload(content=artifact.content, declaration=artifact.declaration))

    def begun(self, identity, artifact, receipt):
        self._at("prepared")
        receipt = DerivedUploadReceipt.model_validate_json(receipt.model_dump_json(warnings=False))
        require(receipt.upload.scope == identity.trace().scope and receipt.upload.content == artifact.content and
                receipt.declaration == artifact.declaration, "publication_upload_binding")
        return replace(self, stage="begun", upload=receipt)

    def start_stream(self):
        self._at("begun")
        return replace(self, stage="streaming")

    def streamed(self, receipt):
        self._at("streaming")
        receipt = UploadContentReceipt.model_validate_json(receipt.model_dump_json(warnings=False))
        require(receipt.upload_id == self.upload.upload.upload_id, "publication_stream_binding")
        return replace(self, stage="streamed", stream=receipt)

    def abandon(self):
        self._at("streaming")
        return replace(self, stage="abandoned")

    def replacement(self, identity):
        self._at("abandoned")
        return PublicationAttempt(AttemptIdentity.for_publication(identity, self.identity.ordinal + 1))

    def start_finalize(self):
        self._at("streamed")
        return replace(self, stage="finalizing")

    def finalize_command(self, identity):
        self._at("finalizing")
        return self.identity.command(identity, "artifacts.finalize", FinalizeArtifact(
            upload_id=self.upload.upload.upload_id, content=self.upload.upload.content))

    def finalized(self, identity, artifact, receipt, derivation):
        self._at("finalizing")
        receipt = FinalizedReceipt.model_validate_json(receipt.model_dump_json(warnings=False))
        derivation = DerivationReceipt.model_validate_json(derivation.model_dump_json(warnings=False))
        ref, expected = receipt.artifact, artifact.content
        begin = self.begin_command(identity, artifact)
        require(self.upload.upload.content == expected and self.upload.declaration == artifact.declaration and
                receipt.upload_id == self.upload.upload.upload_id and ref.scope == identity.trace().scope and
                ref.sha256 == expected.sha256 and ref.size_bytes == expected.size_bytes and
                ref.media_type == expected.media_type and ref.schema_ref == expected.schema_ref and
                derivation.artifact == ref and derivation.upload_id == receipt.upload_id and
                derivation.declaration == artifact.declaration and derivation.origin == begin.identity and
                derivation.request_sha256 == begin.sha256, "publication_finalization_binding")
        return replace(self, stage="finalized", result=derivation)

    def rejected(self, reason):
        require(self.stage in {"prepared", "finalizing"}, "publication_transition")
        TypeAdapter(Identifier).validate_python(reason, strict=True)
        return replace(self, stage="rejected", rejection=reason)
