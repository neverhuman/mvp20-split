"""Explicit scalar checkpoint output, separate from closed authored-address proposals."""

from amphora_contracts_planning import (
    CheckpointDraft,
    MaterializationAdjustmentDraft,
    checkpoint_draft_schema,
)

from ..context.policy import require
from .candidate import CampaignCandidate
from .decision import CampaignDecisionScope
from .output import CampaignOutput


class CheckpointDecisionScope(CampaignDecisionScope):
    profile = staticmethod(checkpoint_draft_schema)

    @classmethod
    def bind(cls, request):
        decision = super().bind(request)
        original = decision.request.document()
        require(original.purpose == 'supervision' and original.runtime_cut is not None, 'checkpoint_output_purpose')
        return decision


class CheckpointCandidate(CampaignCandidate):
    @classmethod
    def bind(cls, draft, decision):
        result = super().bind(draft, decision)
        candidate = draft.candidate
        if isinstance(candidate, MaterializationAdjustmentDraft):
            require(candidate.cut == decision.request.document().runtime_cut, 'checkpoint_adjustment_cut')
            identities = [(item.target.model_dump_json(), item.field_name) for item in candidate.changes]
            require(len(set(identities)) == len(identities), 'checkpoint_duplicate_field')
        return result


class CheckpointOutput(CampaignOutput):
    decision_type = CheckpointDecisionScope
    record_type = CheckpointDraft
    candidate_type = CheckpointCandidate
    profile = staticmethod(checkpoint_draft_schema)
