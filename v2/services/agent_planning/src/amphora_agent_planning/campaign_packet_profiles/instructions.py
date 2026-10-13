"""Closed packaged campaign instruction profile, never selected from owner text."""

import hashlib
from dataclasses import dataclass
from importlib.resources import files

from amphora_contracts_core import ArtifactRef
from amphora_contracts_campaign_curation import campaign_curation_draft_schema

from ..context import RequestSnapshot
from ..context.policy import require


def reviewed_instructions(profile='campaign', version='1'):
    # Canonical LF encoding is part of this owned profile; supplied Artifact bytes
    # are never normalized or repaired to make a different digest pass.
    require(profile in {'campaign', 'curation'}, 'campaign_instruction_profile')
    require(version == '1' or (profile == 'curation' and version in {'2', '3', '4', '5', '6', '7'}), 'campaign_instruction_profile')
    return files(__package__).joinpath('prompts/' + profile + '-v' + version + '.txt').read_bytes().replace(b'\r\n', b'\n')


def reviewed_for_request(request):
    original = request.document()
    profile = 'curation' if original.context.output_schema == campaign_curation_draft_schema() else 'campaign'
    require(profile != 'curation' or original.purpose == 'campaign_proposal', 'curation_instruction_purpose')
    version = '1'
    if profile == 'curation' and original.context.model.provider_id == 'openai':
        from ..curation_input import CurationInputBound
        version = CurationInputBound.bind(original.context.model).envelope_version
    return reviewed_instructions(profile, version)


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
        require(raw == reviewed_for_request(request), 'campaign_instruction_profile')
        return cls(request, reference, raw)
