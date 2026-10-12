"""Durability comes from original immutable output, never a second editable gap."""
from dataclasses import dataclass
import hashlib
import json
import re

from amphora_contracts_campaign_curation import CapabilityRequestRef, CapabilityRequestView, CurationView, CurationRef, CapabilityGap
from ..context.policy import require

REQUEST_ID = re.compile(r'capability-([0-9a-f]{64})-(0[0-9]|1[0-5])\Z')
CURATION_ID = re.compile(r'curation-([0-9a-f]{64})\Z')


@dataclass(frozen=True)
class CapabilityAddress:
    curation_id: str
    ordinal: int

    def __post_init__(self):
        require(type(self.curation_id) is str and CURATION_ID.fullmatch(self.curation_id) is not None
            and type(self.ordinal) is int and 0 <= self.ordinal < 16, 'capability_address')

    @classmethod
    def parse(cls, identifier):
        matched = REQUEST_ID.fullmatch(identifier) if type(identifier) is str else None
        return None if matched is None else cls('curation-' + matched[1], int(matched[2]))

    @property
    def request_id(self):
        matched = CURATION_ID.fullmatch(self.curation_id)
        require(matched is not None and type(self.ordinal) is int and 0 <= self.ordinal < 16,
                'capability_address')
        return 'capability-' + matched[1] + '-' + format(self.ordinal, '02d')


@dataclass(frozen=True)
class OriginalCapability:
    curation: CurationRef
    proposal_sha256: str
    ordinal: int
    gap: CapabilityGap

    @property
    def reference(self):
        return CapabilityRequestRef(scope=self.curation.scope,
            request_id=CapabilityAddress(self.curation.curation_id, self.ordinal).request_id)

    def view(self, fulfillment=None):
        require(fulfillment is None or fulfillment.specification.request == self.reference,
                'capability_fulfillment_request')
        return CapabilityRequestView(reference=self.reference, curation=self.curation,
            proposal_sha256=self.proposal_sha256, gap=self.gap,
            status='fulfilled' if fulfillment is not None and fulfillment.status == 'verified' else 'requested',
            fulfillment=fulfillment)


@dataclass(frozen=True)
class CurationCapabilities:
    requests: tuple[OriginalCapability, ...]

    @classmethod
    def bind(cls, view):
        view = CurationView.model_validate_json(view.model_dump_json())
        if view.proposal is None:
            require(not view.capability_requests, 'capability_original_proposal_missing')
            return cls(())
        require(view.provider is not None and view.provider.output_sha256 is not None,
                'capability_original_capture_missing')
        require(view.provider.attempt.ordinal == 1
            and view.provider.attempt.engagement.scope == view.receipt.reference.scope
            and view.provider.attempt.engagement.engagement_id == 'curation-call-' + view.receipt.request_sha256,
            'capability_original_attempt')
        gaps = getattr(view.proposal.outcome, 'gaps', ())
        require(len({gap.gap_key for gap in gaps}) == len(gaps), 'capability_duplicate_gap')
        raw = json.dumps(view.proposal.model_dump(mode='json'), sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode('utf-8')
        digest = hashlib.sha256(raw).hexdigest()
        result = cls(tuple(OriginalCapability(view.receipt.reference, digest, index, gap)
            for index, gap in enumerate(gaps)))
        require(not view.capability_requests or view.capability_requests == result.references,
                'capability_original_references')
        return result

    @property
    def references(self):
        return tuple(request.reference for request in self.requests)

    @classmethod
    def enrich(cls, view):
        projection = cls.bind(view)
        return CurationView.model_validate_json(view.model_copy(update={
            'capability_requests': projection.references}).model_dump_json())

    def at(self, address):
        if address.ordinal >= len(self.requests):
            return None
        result = self.requests[address.ordinal]
        require(result.curation.curation_id == address.curation_id, 'capability_original_curation')
        return result
