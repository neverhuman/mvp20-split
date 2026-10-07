"""Reconstruct a typed public campaign candidate from exact captured bytes."""

import hashlib
import json

from amphora_contracts_core import Scope, WireModel
from amphora_contracts_planning import (
    CampaignDraft,
    CheckpointDraft,
    CheckpointFollowupDraft,
    campaign_draft_schema,
    checkpoint_draft_schema,
    checkpoint_followup_draft_schema,
)

from ..supervision_requests.binding import encoded
from ..supervision_scope.observations import require
from .followup import validate_followup


def unique(pairs):
    values = {}
    for key, value in pairs:
        require(key not in values, 'duplicate_output_key')
        values[key] = value
    return values


def finite(value):
    raise ValueError('nonfinite_output')


def proposal_from_capture(original, observation, raw):
    proposal = observation.proposal
    require(raw and observation.output_complete and proposal is not None and observation.reason_code is None,
            'successful_capture_incomplete')
    profile = original.context.output_schema
    require(profile in (campaign_draft_schema(), checkpoint_draft_schema(), checkpoint_followup_draft_schema()) and
            proposal.output_schema == original.context.output_schema, 'output_profile_mismatch')
    model = (CheckpointFollowupDraft if profile == checkpoint_followup_draft_schema() else
             CheckpointDraft if profile == checkpoint_draft_schema() else CampaignDraft)
    if model in (CheckpointDraft, CheckpointFollowupDraft):
        require(original.purpose == 'supervision' and original.runtime_cut is not None, 'checkpoint_output_purpose')
    try:
        document = json.loads(raw.decode('utf-8'), object_pairs_hook=unique, parse_constant=finite)
        draft = model.model_validate_json(json.dumps(document, allow_nan=False))
        payload = encoded(draft)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError('invalid_campaign_capture') from error
    require(len(payload) <= 65536, 'interpreted_output_limit')
    require(proposal.payload_json.encode('utf-8') == payload and
            proposal.payload_sha256 == hashlib.sha256(payload).hexdigest() and
            proposal.action == draft.action and proposal.rationale == draft.rationale, 'proposal_capture_mismatch')
    require(draft.decision_scope == original.decision_scope, 'declaration_digest_mismatch')
    require(draft.action in original.context.allowed_actions, 'action_not_allowed')
    require((observation.status == 'abstained') == (draft.action == 'abstain'), 'observation_action_mismatch')
    if draft.action == 'abstain':
        require(draft.candidate is None and not draft.evidence_requests, 'abstention_payload_mismatch')
    elif draft.action == 'request_evidence':
        require(draft.candidate is None and bool(draft.evidence_requests), 'evidence_payload_mismatch')
    else:
        require(draft.candidate is not None, 'campaign_candidate_missing')
    if isinstance(draft, CheckpointFollowupDraft):
        validate_followup(original, draft)
    if draft.candidate is not None and draft.candidate.kind == 'declared_adjustment':
        require(draft.candidate.cut == original.runtime_cut, 'adjustment_cut_mismatch')
        identities = [(tuple(change.target.scope_path), change.target.node_id, change.input_name)
                      for change in draft.candidate.changes]
        require(len(set(identities)) == len(identities), 'duplicate_adjustment')
    if draft.candidate is not None and draft.candidate.kind == 'materialization_adjustment':
        require(draft.candidate.cut == original.runtime_cut, 'adjustment_cut_mismatch')
        identities = [(change.target.model_dump_json(), change.field_name) for change in draft.candidate.changes]
        require(len(set(identities)) == len(identities), 'duplicate_adjustment')
    pending = [draft]
    while pending:
        item = pending.pop()
        if isinstance(item, Scope):
            require(item == original.reference.scope, 'candidate_scope_mismatch')
        elif isinstance(item, WireModel):
            pending.extend(getattr(item, field) for field in type(item).model_fields)
        elif isinstance(item, tuple):
            pending.extend(item)
    return draft
