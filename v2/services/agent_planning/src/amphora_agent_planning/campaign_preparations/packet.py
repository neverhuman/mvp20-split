"""Exact retained packet profile, request, reviewed instructions and measured fit."""

from dataclasses import dataclass

from ..campaign_context.records import canonical
from ..campaign_packet_profiles import CampaignInstructions, PacketBudget
from ..context import RequestSnapshot
from ..context.policy import require
from .encoding import decode, keys


@dataclass(frozen=True)
class PacketEvidence:
    request: RequestSnapshot
    canonical: bytes
    fit_bytes: bytes

    @classmethod
    def bind(cls, request, raw):
        budget = PacketBudget.bind(request)
        request = budget.request
        value = decode(raw, 8388608)
        keys(value, ('format', 'trusted_instructions', 'instruction_reference', 'untrusted_context', 'authority'))
        require(value['format'] == 'planning-campaign-packet.v1' and value['authority'] == 'proposal_input_only',
                'campaign_preparation_packet_profile')
        reference = request.document().context.prompt
        require(canonical(value['instruction_reference']) == canonical(reference.model_dump(mode='json')) and
                type(value['trusted_instructions']) is str, 'campaign_preparation_instruction_reference')
        CampaignInstructions.bind(request, reference, value['trusted_instructions'].encode('utf-8'))
        context = value['untrusted_context']
        keys(context, ('request', 'slices', 'original_omissions', 'budget_omissions', 'consumed_observations'))
        require(canonical(context['request']) == request.canonical, 'campaign_preparation_request')
        require(canonical(context['original_omissions']) == canonical(
            [row.model_dump(mode='json') for row in request.document().context.omissions]), 'campaign_preparation_original_omissions')
        fit = budget.inspect(raw)
        require(fit.fits, 'campaign_preparation_fit')
        return cls(request, raw, canonical(fit.document()))

    def summary(self):
        fit = decode(self.fit_bytes, 8192)
        return {'sha256': fit['packet_sha256'], 'size_bytes': fit['packet_bytes'], 'fit': fit}

    def context(self):
        return decode(self.canonical, 8388608)['untrusted_context']
