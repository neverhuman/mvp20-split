"""Explicit producer-declared lineage; Data owns identity and current-use checks."""

from typing import Annotated, Literal

from amphora_contracts_commands import CommandIdentity
from amphora_contracts_core import ArtifactRef, Digest, Identifier, WireModel
from pydantic import Field

from .models import ContentDescriptor, PublicationPending, PublicationRejected, UploadReceipt


class TransformationDescriptor(WireModel):
    """Pinned producer method/configuration digest, not a scientific attestation."""

    transformation_id: Identifier
    version: Identifier
    sha256: Digest


class DerivationDeclaration(WireModel):
    schema_version: Literal["1"] = "1"
    transformation: TransformationDescriptor
    inputs: Annotated[tuple[ArtifactRef, ...], Field(min_length=1, max_length=128)]


class BeginDerivedUpload(WireModel):
    content: ContentDescriptor
    declaration: DerivationDeclaration


class DerivedUploadReceipt(WireModel):
    schema_version: Literal["1"] = "1"
    upload: UploadReceipt
    declaration: DerivationDeclaration


class DerivedUploadAccepted(WireModel):
    status: Literal["derived_uploaded"] = "derived_uploaded"
    receipt: DerivedUploadReceipt


class DerivedUploadObservation(WireModel):
    schema_version: Literal["1"] = "1"
    identity: CommandIdentity
    operation_id: Identifier
    request_sha256: Digest
    outcome: Annotated[PublicationPending | PublicationRejected | DerivedUploadAccepted,
                       Field(discriminator="status")]


class DerivationReceipt(WireModel):
    """Immutable finalized lineage; reading it does not grant payload access."""

    schema_version: Literal["1"] = "1"
    origin: CommandIdentity
    request_sha256: Digest
    upload_id: Identifier
    artifact: ArtifactRef
    declaration: DerivationDeclaration
