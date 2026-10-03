"""Finite Artifact-only publication state, isolated from the assessment receipt policy."""
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

from .artifact import ScientificPublicationError, canonical, require


def parsed(model, data):
    return model.model_validate_json(canonical(data,2097152))


@dataclass(frozen=True, slots=True)
class ScientificProgress:
    artifact: object
    publisher: str
    position: int = 0
    ordinal: int = 1
    stage: str = "prepared"
    upload: DerivedUploadReceipt | None = None
    derivation: DerivationReceipt | None = None
    failure: str | None = None

    @property
    def scope(self):
        return self.artifact.scope

    def command_id(self, family):
        identity = canonical({"profile":"research.scientific-publication.v1","scope":self.scope.model_dump(mode="json"),
            "kind":self.artifact.kind,"record_id":self.artifact.record_id,"payload_sha256":self.artifact.content.sha256,
            "publisher":self.publisher,"ordinal":self.ordinal,"family":family},4096)
        return hashlib.sha256(identity).hexdigest()

    def command(self, family):
        require(family in ("artifacts.begin_derived_upload","artifacts.finalize"),"science_publication_command_family")
        payload = (BeginDerivedUpload(content=self.artifact.content,declaration=self.artifact.declaration)
            if family == "artifacts.begin_derived_upload" else FinalizeArtifact(upload_id=self.upload.upload.upload_id,content=self.artifact.content))
        return WorkerIdentity(self.publisher,self.scope).command(family,self.command_id(family),payload)

    def advance(self, action, data=None):
        result = replace(self,position=self.position+1)
        if action == "begun" and self.stage == "prepared":
            upload = parsed(DerivedUploadReceipt,data)
            require(upload.upload.scope == self.scope and upload.upload.content == self.artifact.content
                    and upload.declaration == self.artifact.declaration,"science_publication_upload_mismatch")
            return replace(result,stage="begun",upload=upload)
        if action == "streaming" and self.stage == "begun" and data is None:
            return replace(result,stage="streaming")
        if action == "streamed" and self.stage == "streaming":
            receipt = parsed(UploadContentReceipt,data)
            require(receipt.upload_id == self.upload.upload.upload_id,"science_publication_stream_mismatch")
            return replace(result,stage="streamed")
        if action == "replace_uncertain_stream" and self.stage == "streaming" and data is None:
            return (replace(result,stage="failed",failure="science_publication_attempt_limit") if self.ordinal == 8 else
                    replace(result,stage="prepared",ordinal=self.ordinal+1,upload=None))
        if action == "finalizing" and self.stage == "streamed" and data is None:
            return replace(result,stage="finalizing")
        if action == "denied" and self.stage == "prepared" and isinstance(data,str):
            return replace(result,stage="failed",failure=data)
        if action == "rejected" and self.stage in ("prepared","finalizing"):
            family = "artifacts.begin_derived_upload" if self.stage == "prepared" else "artifacts.finalize"
            model = DerivedUploadObservation if self.stage == "prepared" else PublicationObservation
            proof = parsed(model,data)
            command = self.command(family)
            require(proof.identity == command.identity and proof.request_sha256 == command.sha256
                    and proof.outcome.status == "rejected","science_publication_rejection_mismatch")
            return replace(result,stage="failed",failure=proof.outcome.reason_code)
        if action == "published" and self.stage == "finalizing":
            require(type(data) is dict and set(data) == {"finalized","derivation"},"science_publication_terminal_shape")
            final = parsed(FinalizedReceipt,data["finalized"])
            derivation = parsed(DerivationReceipt,data["derivation"])
            command = self.command("artifacts.begin_derived_upload")
            require(final.upload_id == self.upload.upload.upload_id and derivation.upload_id == final.upload_id
                    and final.artifact == derivation.artifact and derivation.origin == command.identity
                    and derivation.request_sha256 == command.sha256,"science_publication_finalization_mismatch")
            self.artifact.verify_derivation(self.publisher,derivation)
            return replace(result,stage="published",derivation=derivation)
        raise ScientificPublicationError("science_publication_transition_invalid")
