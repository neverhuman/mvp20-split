"""Explicit deterministic checkpoint adapter; no model, network or scientific authority."""

import time
from dataclasses import dataclass

from amphora_contracts_planning import CheckpointDraft

from ..context.policy import require
from ..providers.capture import unknown_usage
from ..providers.port import ProviderReply, ProviderUnavailable


@dataclass(frozen=True)
class CheckpointFixture:
    variant: str

    def __post_init__(self):
        require(self.variant in {'fixture_abstain', 'fixture_invalid'}, 'checkpoint_fixture_variant')

    def supports(self, model):
        return (model.provider_id, model.model_id, model.model_revision) == (
            'deterministic', 'adversarial-fixture', '1')

    def reply(self, binding, packet, *, deadline_unix_ms):
        require(type(packet) is bytes and bool(packet), 'checkpoint_fixture_packet')
        if time.time() * 1000 >= deadline_unix_ms:
            raise ProviderUnavailable()
        if self.variant == 'fixture_invalid':
            raw = b'{'
        else:
            document = CheckpointDraft(authority='proposal_only', scientific_authority='not_established',
                action='abstain', rationale='Deterministic software fixture; no scientific assessment.',
                decision_scope=binding.request.document().decision_scope, candidate=None,
                evidence_requests=(), alternatives=(), unresolved=())
            raw = document.model_dump_json().encode('utf-8')
        return ProviderReply((raw,), unknown_usage())
