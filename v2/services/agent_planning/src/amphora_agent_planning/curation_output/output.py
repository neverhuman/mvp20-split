"""Byte-owned curation output with an explicit compiler review projection."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_campaign_curation import CampaignCurationDraft, campaign_curation_draft_schema
from amphora_contracts_planning import CampaignDraft, TypedProposal
from pydantic import ValidationError

from ..campaign_output.decision import CampaignDecisionScope
from ..context import RequestSnapshot
from ..context.policy import require
from ..context.snapshot import _constant, _object


@dataclass(frozen=True)
class CurationOutput:
    request: RequestSnapshot
    canonical: bytes

    @classmethod
    def parse(cls, raw, request):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose == 'campaign_proposal', 'curation_output_purpose')
        require(original.context.output_schema == campaign_curation_draft_schema(), 'curation_output_profile')
        require(type(raw) is bytes and 0 < len(raw) <= 65536, 'typed_output_size')
        try:
            value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
            draft = CampaignCurationDraft.model_validate_json(json.dumps(value, allow_nan=False))
            canonical = json.dumps(draft.model_dump(mode='json'), sort_keys=True, separators=(',', ':'),
                                   ensure_ascii=False, allow_nan=False).encode()
        except (UnicodeError, json.JSONDecodeError, ValidationError, RecursionError) as exc:
            raise ValueError('invalid_curation_output') from exc
        require(len(canonical) <= 65536, 'typed_output_size')
        require(draft.decision_scope == original.decision_scope, 'campaign_decision_scope')
        CampaignDecisionScope._references(draft, original.reference.scope)
        # Generic provider observation records whether there is an executable
        # proposal. Capability requests remain fully typed in the original payload.
        action = 'propose_campaign' if draft.outcome.kind == 'propose_campaign' else 'abstain'
        require(action in original.context.allowed_actions, 'action_not_allowed')
        gaps = getattr(draft.outcome, 'gaps', ())
        require(len({gap.gap_key for gap in gaps}) == len(gaps), 'duplicate_capability_gap')
        for gap in gaps:
            for ports in (gap.inputs, gap.outputs):
                require(len({port.name for port in ports}) == len(ports), 'duplicate_capability_port')
        return cls(request, canonical)

    def document(self):
        return CampaignCurationDraft.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    @property
    def action(self):
        return 'propose_campaign' if self.document().outcome.kind == 'propose_campaign' else 'abstain'

    def proposal(self):
        require(self.parse(self.canonical, self.request) == self, 'curation_output_binding')
        return TypedProposal(output_schema=campaign_curation_draft_schema(), action=self.action,
            rationale=self.document().rationale, payload_json=self.canonical.decode(), payload_sha256=self.sha256)

    def review_document(self):
        """Internal compatibility projection, never a replacement provider capture."""
        checked = self.parse(self.canonical, self.request)
        require(checked == self, 'curation_output_binding')
        draft = checked.document()
        candidate = draft.outcome.candidate if draft.outcome.kind == 'propose_campaign' else None
        return CampaignDraft(authority=draft.authority, scientific_authority=draft.scientific_authority,
            action=checked.action, rationale=draft.rationale, decision_scope=draft.decision_scope,
            candidate=candidate, evidence_requests=(), alternatives=(), unresolved=draft.unresolved)
