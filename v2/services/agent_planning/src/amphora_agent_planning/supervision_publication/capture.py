"""Byte-owned observation provenance; factories do not prove SQL or fresh rights."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_artifacts import (
    ContentDescriptor,
    DerivationDeclaration,
    TransformationDescriptor,
)
from amphora_contracts_core import ArtifactRef, SchemaRef
from amphora_contracts_planning import checkpoint_followup_draft_schema

from ..context import AttemptBinding
from ..context.policy import require
from ..campaign_followup.prepared import PreparedFollowupProposal
from ..persistence.records import verified_observation
from ..providers.capture import Observation
from ..supervision_execution.packet import CheckpointPacket

OPAQUE_SCHEMA = b'{"type":"string","contentEncoding":"base64"}'


def capture_schema():
    return SchemaRef(schema_id='planning.supervision-capture', version='1',
        sha256=hashlib.sha256(OPAQUE_SCHEMA).hexdigest())


@dataclass(frozen=True)
class CaptureOrigin:
    packet: CheckpointPacket
    observation: Observation
    kind: str = 'primary'

    @classmethod
    def bind(cls, intake, principal, preparation, observation, *, kind='primary'):
        require(kind in {'primary', 'late'}, 'capture_observation_kind')
        packet = CheckpointPacket.bind(intake, principal, preparation)
        binding = AttemptBinding(packet.context.snapshot.planning, observation.document().attempt.ordinal)
        observed = verified_observation(binding, observation)
        require(observed == observation, 'capture_observation_canonical')
        if (binding.request.document().context.output_schema == checkpoint_followup_draft_schema() and
                observed.document().status in {'proposed', 'abstained'}):
            PreparedFollowupProposal.bind(preparation, binding, observed)
        return cls(packet, observed, kind)

    @property
    def scope(self):
        return self.packet.context.snapshot.planning.document().reference.scope

    def inputs(self):
        rows = self.packet.preparation.packet.context()['slices']
        values = tuple(ArtifactRef.model_validate(row['identity']) for row in rows
            if row['lane'] == 'artifact' and row['payload']['status'] == 'available')
        require(0 < len(values) <= 128, 'capture_derivation_input_limit')
        return tuple(sorted(values, key=lambda ref: ref.artifact_id))


@dataclass(frozen=True)
class CaptureArtifact:
    body: bytes
    content: ContentDescriptor
    declaration: DerivationDeclaration

    @classmethod
    def bind(cls, origin):
        raw = origin.observation.capture.content
        require(0 < len(raw) <= 65536, 'capture_publication_nonempty')
        packet = origin.packet.preparation
        method = b'planning.checkpoint-capture.v1\n' + b'\n'.join(value.encode('ascii') for value in (
            origin.packet.context.snapshot.sha256, packet.sha256,
            hashlib.sha256(origin.observation.canonical).hexdigest()))
        descriptor = ContentDescriptor(sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw),
            media_type='application/octet-stream', schema_ref=capture_schema())
        declaration = DerivationDeclaration(transformation=TransformationDescriptor(
            transformation_id='planning.checkpoint_capture', version='1', sha256=hashlib.sha256(method).hexdigest()),
            inputs=origin.inputs())
        return cls(raw, descriptor, declaration)

    def require_reference(self, scope, reference):
        ref = ArtifactRef.model_validate(reference.model_dump(mode='python', warnings=False))
        require(ref.scope == scope and ref.sha256 == self.content.sha256 and
            ref.size_bytes == self.content.size_bytes and ref.media_type == self.content.media_type and
            ref.schema_ref == self.content.schema_ref, 'capture_publication_reference')
        return ref
