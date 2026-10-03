"""Verify declared/finalized identities before projecting a source binding."""

from dataclasses import dataclass

from amphora_contracts_artifacts import DerivationReceipt, DerivedUploadObservation
from amphora_contracts_representations import RepresentationBinding, RepresentationBindingRef

from ..mapping import _validated
from ..validation import fingerprint, require
from .document import VectorPublication


@dataclass(frozen=True, slots=True)
class BindingReceipts:
    publication: VectorPublication
    attempt: int = 1

    def __post_init__(self):
        require(type(self.publication) is VectorPublication, "representation_publication_required")
        self.publication.identity.command_id("begin", self.attempt)

    def upload(self, observation):
        observation = _validated(observation, DerivedUploadObservation)
        command = self.publication.command("begin", attempt=self.attempt)
        require(
            observation.identity == command.identity and observation.request_sha256 == command.sha256,
            "representation_upload_identity",
        )
        require(observation.outcome.status == "derived_uploaded", "representation_upload_pending")
        receipt = observation.outcome.receipt
        identity = self.publication.identity
        require(
            receipt.upload.scope == identity.scope and receipt.upload.content == self.publication.content,
            "representation_upload_receipt",
        )
        require(receipt.declaration == self.publication.declaration, "representation_derivation_receipt")
        return receipt.upload.upload_id

    def finalized(self, upload_id, receipt):
        receipt = _validated(receipt, DerivationReceipt)
        identity = self.publication.identity
        command = self.publication.command("begin", attempt=self.attempt)
        require(
            receipt.origin == command.identity
            and receipt.request_sha256 == command.sha256
            and receipt.upload_id == upload_id,
            "representation_derivation_identity",
        )
        require(receipt.declaration == self.publication.declaration, "representation_derivation_receipt")
        content = self.publication.content
        artifact = receipt.artifact
        require(
            artifact.artifact_id != identity.source.source.raw.artifact_id, "representation_self_derivation"
        )
        require(
            artifact.scope == identity.scope
            and (artifact.sha256, artifact.size_bytes, artifact.media_type, artifact.schema_ref)
            == (content.sha256, content.size_bytes, content.media_type, content.schema_ref),
            "representation_vector_artifact",
        )
        body = {
            "format": "data.representation-binding.v1",
            "binding_id": identity.binding_id,
            "scope": identity.scope.model_dump(mode="json"),
            "profile": identity.profile.model_dump(mode="json"),
            "source": identity.source.model_dump(mode="json"),
            "vector": artifact.model_dump(mode="json"),
        }
        reference = RepresentationBindingRef(
            scope=identity.scope, binding_id=identity.binding_id, sha256=fingerprint(body)
        )
        return RepresentationBinding(
            wire_version="1",
            reference=reference,
            profile=identity.profile,
            source=identity.source,
            vector=artifact,
        )
