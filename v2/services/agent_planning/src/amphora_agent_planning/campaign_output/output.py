"""Bounded byte-owned campaign output; exact raw capture remains provider-owned."""

import hashlib
import json
from dataclasses import dataclass
from typing import ClassVar

from amphora_contracts_planning import (
    CampaignDraft,
    TypedProposal,
    campaign_draft_schema,
)
from pydantic import ValidationError

from ..context.policy import require
from ..context.snapshot import _constant, _object
from .candidate import CampaignCandidate
from .decision import CampaignDecisionScope

MAX_OUTPUT_BYTES = 65536


@dataclass(frozen=True)
class CampaignOutput:
    decision: CampaignDecisionScope
    canonical: bytes
    decision_type: ClassVar = CampaignDecisionScope
    record_type: ClassVar = CampaignDraft
    candidate_type: ClassVar = CampaignCandidate
    profile: ClassVar = staticmethod(campaign_draft_schema)

    @classmethod
    def parse(cls, raw, request):
        decision = cls.decision_type.bind(request)
        require(type(raw) is bytes and 0 < len(raw) <= MAX_OUTPUT_BYTES, 'typed_output_size')
        try:
            value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
            draft = cls.record_type.model_validate_json(json.dumps(value, allow_nan=False))
            canonical = json.dumps(draft.model_dump(mode='json'), sort_keys=True, separators=(',', ':'),
                                   ensure_ascii=False, allow_nan=False).encode('utf-8')
        except (UnicodeError, json.JSONDecodeError, ValidationError, RecursionError) as exc:
            raise ValueError('invalid_output') from exc
        require(len(canonical) <= MAX_OUTPUT_BYTES, 'typed_output_size')
        decision.validate(draft)
        cls.candidate_type.bind(draft, decision)
        return cls(decision, canonical)

    def document(self):
        return self.record_type.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def proposal(self):
        # Reconstruct even for directly constructed/modified domain values.
        checked = self.parse(self.canonical, self.decision.request)
        require(checked == self, 'campaign_output_binding')
        draft = checked.document()
        return TypedProposal(output_schema=self.profile(), action=draft.action,
                             rationale=draft.rationale, payload_json=checked.canonical.decode('utf-8'),
                             payload_sha256=checked.sha256)
