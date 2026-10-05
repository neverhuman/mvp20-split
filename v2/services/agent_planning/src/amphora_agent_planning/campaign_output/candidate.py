"""Candidate shape/action consistency is separate from semantic eligibility."""

from dataclasses import dataclass

from amphora_contracts_planning import CampaignAdjustmentDraft

from ..context.policy import require


@dataclass(frozen=True)
class CampaignCandidate:
    kind: str | None

    @classmethod
    def bind(cls, draft, decision):
        candidate = draft.candidate
        if draft.action == 'abstain':
            require(candidate is None and not draft.evidence_requests, 'campaign_abstention_payload')
        elif draft.action == 'request_evidence':
            require(candidate is None and bool(draft.evidence_requests), 'campaign_evidence_payload')
        else:
            require(candidate is not None, 'campaign_missing_candidate')
        if isinstance(candidate, CampaignAdjustmentDraft):
            original = decision.request.document()
            require(original.purpose == 'supervision' and original.runtime_cut is not None,
                    'campaign_adjustment_purpose')
            require(candidate.cut == original.runtime_cut, 'campaign_adjustment_cut')
            identities = set()
            for change in candidate.changes:
                identity = (*change.target.scope_path, change.target.node_id, change.input_name)
                require(identity not in identities, 'campaign_duplicate_adjustment')
                identities.add(identity)
        return cls(None if candidate is None else candidate.kind)
