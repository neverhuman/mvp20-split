"""Measured packet ceilings preserve original request limits; no spend reservation."""

from dataclasses import dataclass

from ..context import RequestSnapshot
from ..context.policy import require
from .tokenizer import FixturePacketTokenizer, PacketMeasurement


@dataclass(frozen=True)
class PacketBudget:
    request: RequestSnapshot
    tokenizer: FixturePacketTokenizer

    @classmethod
    def bind(cls, request):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {'campaign_proposal', 'supervision'}, 'campaign_packet_purpose')
        return cls(request, FixturePacketTokenizer.bind(original.context.model))

    def inspect(self, raw):
        bound = self.bind(self.request)
        require(bound == self, 'campaign_packet_budget_binding')
        measured = self.tokenizer.measure(raw)
        context = self.request.document().context
        # Request binding already proves input ceiling + reserved output fits
        # both the original window and total ceiling. Do not invent spare budget.
        reason = 'input_limit' if measured.input_tokens > context.limits.max_input_tokens else None
        return PacketFit(self, measured, reason)


@dataclass(frozen=True)
class PacketFit:
    budget: PacketBudget
    measurement: PacketMeasurement
    reason: str | None

    @property
    def fits(self):
        return self.reason is None

    def document(self):
        context = self.budget.request.document().context
        return {'format': 'planning-campaign-packet-fit.v1', 'request_sha256': self.budget.request.sha256,
            'tokenizer': self.budget.tokenizer.reference.model_dump(mode='json'), 'unit': 'synthetic_byte_token',
            'framing': 'exact_packet_bytes', 'packet_sha256': self.measurement.sha256,
            'packet_bytes': self.measurement.size_bytes, 'input_tokens': self.measurement.input_tokens,
            'output_reserve': context.limits.max_output_tokens, 'input_limit': context.limits.max_input_tokens,
            'window_limit': context.model.context_window_tokens, 'original_total_limit': context.limits.total_tokens,
            'fits': self.fits, 'reason': self.reason, 'authorization': 'none'}
