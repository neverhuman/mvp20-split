"""Immutable private preparation evidence; storage/dispatch authority is separate."""

import hashlib
from dataclasses import dataclass
from functools import lru_cache

from ..campaign_context.records import canonical
from ..campaign_packet import reconstruct
from ..context.policy import require
from ..context import RequestSnapshot
from .encoding import decode
from .inputs import PreparationInputs
from .packet import PacketEvidence
from .wire import PreparationRecord


@dataclass(frozen=True)
class CampaignPreparation:
    packet: PacketEvidence
    canonical: bytes

    @classmethod
    def bind(cls, plan, packet):
        verified = reconstruct(plan, packet.canonical, plan_sha256=packet.plan_sha256, packet_sha256=packet.sha256)
        require(verified == packet, 'campaign_preparation_packet_binding')
        evidence = PacketEvidence.bind(plan.request, verified.canonical)
        value = {'profile': 'planning-campaign-preparation.v1', 'authority': 'historical_input_only',
            'engagement': plan.request.document().reference.model_dump(mode='json'), 'request_sha256': plan.request.sha256,
            'plan_sha256': plan.sha256, 'packet': evidence.summary(), 'candidates': PreparationInputs.capture(plan, verified).document()}
        return cls.from_bytes(plan.request, canonical(value), verified.canonical)

    @classmethod
    def from_bytes(cls, request, manifest, raw_packet):
        require(isinstance(request, RequestSnapshot) and type(request.canonical) is bytes
                and 0 < len(request.canonical) <= 262144, 'campaign_preparation_request_binding')
        require(type(manifest) is bytes and 0 < len(manifest) <= 2097152
                and type(raw_packet) is bytes and 0 < len(raw_packet) <= 8388608,
                'campaign_preparation_size')
        return cls._verified(request.canonical, manifest, raw_packet)

    @classmethod
    @lru_cache(maxsize=1)
    def _verified(cls, request_bytes, manifest, raw_packet):
        # The key and entire returned object contain immutable bytes only.
        # This validates retained input, never current rights or owner state.
        request = RequestSnapshot(request_bytes)
        value = decode(manifest, 2097152)
        document = PreparationRecord.model_validate_json(canonical(value))
        require(canonical(document.model_dump(mode='json')) == manifest, 'campaign_preparation_manifest_canonical')
        evidence = PacketEvidence.bind(request, raw_packet)
        require(document.engagement == evidence.request.document().reference and
                document.request_sha256 == evidence.request.sha256, 'campaign_preparation_request_binding')
        require(canonical(document.packet.model_dump(mode='json')) == canonical(evidence.summary()), 'campaign_preparation_packet_summary')
        PreparationInputs(document.candidates).verify(evidence.request, evidence.context())
        return cls(evidence, manifest)

    def document(self):
        return PreparationRecord.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
