"""Closed future-only output shape; retained preparation owns criterion membership."""

from amphora_contracts_planning import CheckpointFollowupDraft, checkpoint_followup_draft_schema

from ..campaign_output.decision import CampaignDecisionScope
from ..campaign_output.output import CampaignOutput


class FollowupDecisionScope(CampaignDecisionScope):
    profile = staticmethod(checkpoint_followup_draft_schema)


class FollowupOutput(CampaignOutput):
    decision_type = FollowupDecisionScope
    record_type = CheckpointFollowupDraft
    profile = staticmethod(checkpoint_followup_draft_schema)
