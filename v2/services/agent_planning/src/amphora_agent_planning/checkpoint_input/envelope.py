"""One canonical Responses body shared by pre-issuance fit and later transport."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_planning import CheckpointDraft, checkpoint_draft_schema

from ..campaign_context.records import canonical
from ..context import RequestSnapshot
from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..openai_provider.pricing import MODEL


@dataclass(frozen=True)
class CheckpointEnvelope:
    request_sha256: str
    packet_sha256: str
    packet_bytes: int
    body: bytes

    @classmethod
    def bind(cls, request, raw):
        from ..campaign_packet_profiles.instructions import CampaignInstructions
        from .profile import CheckpointInputBound

        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        CheckpointInputBound.bind(original.context.model)
        require(original.purpose == 'supervision', 'checkpoint_input_purpose')
        require(original.context.output_schema == checkpoint_draft_schema(), 'checkpoint_input_output_profile')
        require(type(raw) is bytes and 0 < len(raw) <= 8388608, 'checkpoint_input_size')
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {
            'format', 'trusted_instructions', 'instruction_reference', 'untrusted_context', 'authority'},
            'checkpoint_input_packet')
        require(canonical(value) == raw, 'checkpoint_input_canonical')
        require(value['format'] == 'planning-campaign-packet.v1' and value['authority'] == 'proposal_input_only',
                'checkpoint_input_packet_profile')
        require(value['instruction_reference'] == original.context.prompt.model_dump(mode='json') and
                type(value['trusted_instructions']) is str, 'checkpoint_input_instruction_reference')
        CampaignInstructions.bind(request, original.context.prompt, value['trusted_instructions'].encode('utf-8'))
        context = value['untrusted_context']
        require(type(context) is dict and set(context) == {
            'request', 'slices', 'original_omissions', 'budget_omissions', 'consumed_observations'},
            'checkpoint_input_context')
        require(canonical(context['request']) == request.canonical, 'checkpoint_input_request')
        require(context['original_omissions'] == [item.model_dump(mode='json') for item in original.context.omissions],
                'checkpoint_input_omissions')
        require(all(type(context[key]) is list for key in ('slices', 'budget_omissions', 'consumed_observations')),
                'checkpoint_input_context')
        # JSON mode is deliberate: arbitrary proposal parameter maps are not a closed
        # provider strict-schema subset. Existing local CheckpointDraft validation
        # remains authoritative. Both schema guidance and all framing count in fit.
        payload = canonical({'output_schema': CheckpointDraft.model_json_schema(mode='validation'),
            'packet_sha256': hashlib.sha256(raw).hexdigest(), 'untrusted_context': context}).decode('utf-8')
        body = canonical({'model': MODEL, 'store': False, 'stream': False, 'service_tier': 'default',
            'reasoning': {'effort': 'low'}, 'max_output_tokens': original.context.limits.max_output_tokens,
            'instructions': value['trusted_instructions'],
            'input': [{'role': 'user', 'content': 'Return JSON only, conforming to output_schema.\n' + payload}],
            'text': {'format': {'type': 'json_object'}}})
        return cls(request.sha256, hashlib.sha256(raw).hexdigest(), len(raw), body)

    @property
    def sha256(self):
        return hashlib.sha256(self.body).hexdigest()

    @property
    def input_bound(self):
        return len(self.body) + 1024
