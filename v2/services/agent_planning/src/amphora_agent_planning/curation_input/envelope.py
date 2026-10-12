"""Exact curation Responses bytes fitted before issuance and replayed unchanged."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_campaign_curation import CampaignCurationDraft, campaign_curation_draft_schema

from ..campaign_context.records import canonical
from ..context import RequestSnapshot
from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..openai_provider.pricing import MODEL


@dataclass(frozen=True)
class CurationEnvelope:
    request_sha256: str
    packet_sha256: str
    packet_bytes: int
    body: bytes

    @classmethod
    def bind(cls, request, raw):
        from ..campaign_packet_profiles.instructions import CampaignInstructions
        from .profile import CurationInputBound

        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        profile = CurationInputBound.bind(original.context.model)
        require(original.purpose == 'campaign_proposal', 'curation_input_purpose')
        require(original.context.output_schema == campaign_curation_draft_schema(), 'curation_input_output_profile')
        require(type(raw) is bytes and 0 < len(raw) <= 8388608, 'curation_input_size')
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {
            'format', 'trusted_instructions', 'instruction_reference', 'untrusted_context', 'authority'},
            'curation_input_packet')
        require(canonical(value) == raw, 'curation_input_canonical')
        require(value['format'] == 'planning-campaign-packet.v1' and value['authority'] == 'proposal_input_only',
                'curation_input_packet_profile')
        require(value['instruction_reference'] == original.context.prompt.model_dump(mode='json')
                and type(value['trusted_instructions']) is str, 'curation_input_instruction_reference')
        CampaignInstructions.bind(request, original.context.prompt, value['trusted_instructions'].encode('utf-8'))
        context = value['untrusted_context']
        require(type(context) is dict and set(context) == {
            'request', 'slices', 'original_omissions', 'budget_omissions', 'consumed_observations'},
            'curation_input_context')
        require(canonical(context['request']) == request.canonical, 'curation_input_request')
        require(context['original_omissions'] == [item.model_dump(mode='json') for item in original.context.omissions],
                'curation_input_omissions')
        require(all(type(context[key]) is list for key in ('slices', 'budget_omissions', 'consumed_observations')),
                'curation_input_context')
        if profile.envelope_version in {'2', '3', '4', '5'}:
            from .readable import readable_context
            context = readable_context(context)
        payload = canonical({'output_schema': CampaignCurationDraft.model_json_schema(mode='validation'),
            'packet_sha256': hashlib.sha256(raw).hexdigest(), 'untrusted_context': context}).decode('utf-8')
        output_format = {'type': 'json_object'}
        if profile.envelope_version in {'3', '4', '5'}:
            from .structured import GenerationSchema
            output_format = GenerationSchema.reviewed().format()
        body = canonical({'model': MODEL, 'store': False, 'stream': False, 'service_tier': 'default',
            'reasoning': {'effort': 'none' if profile.envelope_version in {'4', '5'} else 'low'}, 'max_output_tokens': original.context.limits.max_output_tokens,
            'instructions': value['trusted_instructions'],
            'input': [{'role': 'user', 'content': 'Return JSON only, conforming to output_schema.\n' + payload}],
            'text': {'format': output_format}})
        return cls(request.sha256, hashlib.sha256(raw).hexdigest(), len(raw), body)

    @property
    def sha256(self):
        return hashlib.sha256(self.body).hexdigest()

    @property
    def input_bound(self):
        return len(self.body) + 1024
