"""One explicit upload attempt; uncertain streams never become finalizations."""

import json
import uuid
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

from ..authoring.canonical import KnowledgeError
from ..reasoning.profile import raw


@dataclass(frozen=True)
class AttemptIdentity:
    ordinal: int
    begin_id: str
    finalize_id: str

    @classmethod
    def new(cls, ordinal):
        if type(ordinal) is not int or not 1 <= ordinal <= 8:
            raise KnowledgeError("publication_attempt_limit")
        return cls(ordinal, uuid.uuid4().hex, uuid.uuid4().hex)

    def command(self, publisher, scope, family, payload):
        key = self.begin_id if family == "artifacts.begin_derived_upload" else self.finalize_id
        identity = CommandIdentity(command_family=family, command_id=key, actor_id=publisher.actor_id, scope=scope)
        body = json.dumps({"identity": identity.model_dump(mode="json"), "payload": payload.model_dump(mode="json")})
        return CanonicalCommand.for_family(body, family, type(payload))


@dataclass(frozen=True)
class PublicationAttempt:
    identity: AttemptIdentity
    stage: str = "prepared"
    upload: DerivedUploadReceipt | None = None
    stream: UploadContentReceipt | None = None
    result: DerivationReceipt | None = None

    @classmethod
    def first(cls):
        return cls(AttemptIdentity.new(1))

    def _at(self, stage):
        if self.stage != stage:
            raise KnowledgeError("publication_attempt_transition_invalid")

    def begin_command(self, artifact, publisher):
        return self.identity.command(publisher, artifact.result.request.snapshot.graph.scope,
            "artifacts.begin_derived_upload", BeginDerivedUpload(content=artifact.content, declaration=artifact.declaration))

    def accepted_upload(self, artifact, receipt):
        self._at("prepared")
        receipt = DerivedUploadReceipt.model_validate(raw(receipt))
        if (receipt.upload.scope != artifact.result.request.snapshot.graph.scope
                or receipt.upload.content != artifact.content or receipt.declaration != artifact.declaration):
            raise KnowledgeError("publication_upload_mismatch")
        return replace(self, stage="begun", upload=receipt)

    def start_stream(self):
        self._at("begun")
        return replace(self, stage="streaming")

    def streamed(self, receipt):
        self._at("streaming")
        receipt = UploadContentReceipt.model_validate(raw(receipt))
        if receipt.upload_id != self.upload.upload.upload_id:
            raise KnowledgeError("publication_stream_mismatch")
        return replace(self, stage="streamed", stream=receipt)

    def abandon_stream(self):
        self._at("streaming")
        return replace(self, stage="abandoned")

    def replacement(self):
        self._at("abandoned")
        return PublicationAttempt(AttemptIdentity.new(self.identity.ordinal + 1))

    def start_finalize(self):
        self._at("streamed")
        return replace(self, stage="finalizing")

    def finalize_command(self, publisher):
        self._at("finalizing")
        upload = self.upload.upload
        return self.identity.command(publisher, upload.scope, "artifacts.finalize",
            FinalizeArtifact(upload_id=upload.upload_id, content=upload.content))

    def finalized(self, artifact, publisher, receipt, derivation):
        self._at("finalizing")
        receipt = FinalizedReceipt.model_validate(raw(receipt))
        derivation = DerivationReceipt.model_validate(raw(derivation))
        ref, content = receipt.artifact, artifact.content
        command = self.begin_command(artifact, publisher)
        if (self.upload.upload.content != content or self.upload.declaration != artifact.declaration
                or receipt.upload_id != self.upload.upload.upload_id or ref.scope != self.upload.upload.scope
                or ref.sha256 != content.sha256 or ref.size_bytes != content.size_bytes
                or ref.media_type != content.media_type or ref.schema_ref != content.schema_ref
                or derivation.artifact != ref or derivation.upload_id != receipt.upload_id
                or derivation.declaration != artifact.declaration or derivation.origin != command.identity
                or derivation.request_sha256 != command.sha256):
            raise KnowledgeError("publication_finalization_mismatch")
        return replace(self, stage="finalized", result=derivation)
