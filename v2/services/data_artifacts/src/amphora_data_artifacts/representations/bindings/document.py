"""Exact vector Artifact and source-only derivation recipe, without publication effects."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_artifacts import (
    ContentDescriptor,
    DerivationDeclaration,
    TransformationDescriptor,
    parse_command,
)
from amphora_contracts_representations import representation_vector_schema

from ..mapping import profile_reference, vector_to_wire
from ..payloads import EncodedRepresentation
from ..validation import canonical_record, require
from .identity import SourceBindingIdentity


@dataclass(frozen=True, slots=True)
class VectorPublication:
    identity: SourceBindingIdentity
    encoded: EncodedRepresentation

    def __post_init__(self):
        require(type(self.identity) is SourceBindingIdentity, "representation_binding_required")
        require(type(self.encoded) is EncodedRepresentation, "representation_encoded_required")
        require(
            profile_reference(self.identity.scope, self.encoded.profile) == self.identity.profile,
            "representation_binding_profile",
        )
        require(
            self.encoded.input_sha256 == self.identity.source.sha256 and self.encoded.context_sha256 is None,
            "representation_binding_input",
        )

    @property
    def payload(self):
        return canonical_record(vector_to_wire(self.identity.scope, self.encoded))

    @property
    def content(self):
        payload = self.payload
        return ContentDescriptor(
            sha256=hashlib.sha256(payload).hexdigest(),
            size_bytes=len(payload),
            media_type="application/json",
            schema_ref=representation_vector_schema(),
        )

    @property
    def declaration(self):
        return DerivationDeclaration(
            transformation=TransformationDescriptor(
                transformation_id="data.representation", version="1", sha256=self.identity.sha256
            ),
            inputs=(self.identity.source.source.raw,),
        )

    def command(self, stage, upload_id=None):
        command_id = self.identity.command_id(stage)
        family = "artifacts.begin_derived_upload" if stage == "begin" else "artifacts.finalize"
        payload = {"content": self.content.model_dump(mode="json")}
        if stage == "begin":
            require(upload_id is None, "representation_upload_identity")
            payload["declaration"] = self.declaration.model_dump(mode="json")
        else:
            require(type(upload_id) is str, "representation_upload_identity")
            payload["upload_id"] = upload_id
        raw = {
            "identity": {
                "command_family": family,
                "command_id": command_id,
                "actor_id": self.identity.actor_id,
                "scope": self.identity.scope.model_dump(mode="json"),
            },
            "payload": payload,
        }
        return parse_command(family, json.dumps(raw))
