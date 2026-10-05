"""Closed packaged campaign instruction profile, never selected from owner text."""

import hashlib
from dataclasses import dataclass
from importlib.resources import files

from amphora_contracts_core import ArtifactRef

from ..context import RequestSnapshot
from ..context.policy import require


def reviewed_instructions():
    # Canonical LF encoding is part of this owned profile; supplied Artifact bytes
    # are never normalized or repaired to make a different digest pass.
    return files(__package__).joinpath('prompts/campaign-v1.txt').read_bytes().replace(b'\r\n', b'\n')


@dataclass(frozen=True)
class CampaignInstructions:
    request: RequestSnapshot
    reference: ArtifactRef
    body: bytes

    @classmethod
    def bind(cls, request, reference, raw):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {'campaign_proposal', 'supervision'}, 'campaign_packet_purpose')
        reference = ArtifactRef.model_validate(reference.model_dump(mode='python', warnings=False))
        require(reference == original.context.prompt, 'campaign_instruction_binding')
        require(type(raw) is bytes and 0 < len(raw) <= 65536 and reference.media_type == 'text/plain' and
                reference.size_bytes == len(raw) and reference.sha256 == hashlib.sha256(raw).hexdigest(), 'campaign_instruction_digest')
        require(raw == reviewed_instructions(), 'campaign_instruction_profile')
        return cls(request, reference, raw)
