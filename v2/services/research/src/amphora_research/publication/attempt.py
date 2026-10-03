"""Finite publication transitions with stable command identities and retained uncertainty."""

import hashlib
from dataclasses import dataclass, replace

from amphora_contracts_artifacts import (
    BeginDerivedUpload,
    DerivationReceipt,
    DerivedUploadObservation,
    DerivedUploadReceipt,
    FinalizeArtifact,
    FinalizedReceipt,
    PublicationObservation,
    UploadContentReceipt,
)
from amphora_tool_protocol import WorkerIdentity

from ..assessment.policy import AssessmentError
from ..assessment.store import canonical
from .artifact import SyntheticReceiptPolicy


def parsed(model, data):
    return model.model_validate_json(canonical(data, 2097152))


@dataclass(frozen=True)
class PublicationProgress:
    artifact: object
    publisher: str
    issuer: str
    position: int = 0
    ordinal: int = 1
    stage: str = "prepared"
    upload: DerivedUploadReceipt | None = None
    derivation: DerivationReceipt | None = None
    receipt: object = None
    failure: str | None = None

    @property
    def scope(self):
        return self.artifact.stored.intent.bound.request.profile.scope

    def command_id(self, family):
        identity = canonical({"scope": self.scope.model_dump(mode="json"),
            "assessment": self.artifact.stored.intent.bound.request.assessment_id,
            "publisher": self.publisher, "ordinal": self.ordinal, "family": family}, 4096)
        return hashlib.sha256(identity).hexdigest()

    def command(self, family):
        payload = (BeginDerivedUpload(content=self.artifact.content, declaration=self.artifact.declaration)
                   if family == "artifacts.begin_derived_upload" else
                   FinalizeArtifact(upload_id=self.upload.upload.upload_id, content=self.artifact.content))
        return WorkerIdentity(self.publisher, self.scope).command(family, self.command_id(family), payload)

    def advance(self, action, data=None):
        result = replace(self, position=self.position + 1)
        if action == "begun" and self.stage == "prepared":
            upload = parsed(DerivedUploadReceipt, data)
            if (upload.upload.scope != self.scope or upload.upload.content != self.artifact.content
                    or upload.declaration != self.artifact.declaration):
                raise AssessmentError("publication_upload_mismatch")
            return replace(result, stage="begun", upload=upload)
        if action == "streaming" and self.stage == "begun" and data is None:
            return replace(result, stage="streaming")
        if action == "streamed" and self.stage == "streaming":
            receipt = parsed(UploadContentReceipt, data)
            if receipt.upload_id != self.upload.upload.upload_id:
                raise AssessmentError("publication_stream_mismatch")
            return replace(result, stage="streamed")
        if action == "replace_uncertain_stream" and self.stage == "streaming" and data is None:
            if self.ordinal == 8:
                return replace(result, stage="failed", failure="publication_stream_attempt_limit")
            return replace(result, stage="prepared", ordinal=self.ordinal + 1, upload=None)
        if action == "finalizing" and self.stage == "streamed" and data is None:
            return replace(result, stage="finalizing")
        if action == "denied" and self.stage == "prepared" and isinstance(data, str):
            return replace(result, stage="failed", failure=data)
        if action == "rejected" and self.stage in {"prepared", "finalizing"}:
            family = "artifacts.begin_derived_upload" if self.stage == "prepared" else "artifacts.finalize"
            model = DerivedUploadObservation if self.stage == "prepared" else PublicationObservation
            proof = parsed(model, data)
            command = self.command(family)
            if (proof.identity != command.identity or proof.request_sha256 != command.sha256
                    or proof.outcome.status != "rejected"):
                raise AssessmentError("publication_rejection_mismatch")
            return replace(result, stage="failed", failure=proof.outcome.reason_code)
        if action == "published" and self.stage == "finalizing":
            finalized = parsed(FinalizedReceipt, data["finalized"])
            derivation = parsed(DerivationReceipt, data["derivation"])
            command = self.command("artifacts.begin_derived_upload")
            if (finalized.upload_id != self.upload.upload.upload_id or derivation.upload_id != finalized.upload_id
                    or finalized.artifact != derivation.artifact or derivation.origin != command.identity
                    or derivation.request_sha256 != command.sha256):
                raise AssessmentError("publication_finalization_mismatch")
            receipt = SyntheticReceiptPolicy().issue(self.artifact, self.publisher, self.issuer, derivation)
            if data["receipt"] != receipt.model_dump(mode="json"):
                raise AssessmentError("publication_receipt_mismatch")
            return replace(result, stage="published", derivation=derivation, receipt=receipt)
        raise AssessmentError("publication_transition_invalid")
