"""Synthetic public intent; criterion membership is tested by its Planning owner."""

import copy
import hashlib
import json

from amphora_campaign_runtime.supervision_requests.binding import CheckpointRequestBinding
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_contracts_planning import CheckpointFollowupDraft, checkpoint_followup_draft_schema
from amphora_contracts_supervision import CheckpointRequest, SupervisionResponse

from ..supervision_responses.test_checkpoint_output import exchange as predecessor_exchange


def draft(scope, decision, *, action='request_evidence', definition=None):
    point = {'question': {'scope': scope, 'question_id': 'question', 'revision': 1},
        'need': {'scope': scope, 'need_id': 'need', 'revision': 1}, 'criterion_id': 'criterion', 'assessment': None}
    intent = {'question': point['question'], 'needs': [point['need']], 'assessments': [],
        'producer': None, 'expected_evidence': 'A more informative next campaign', 'uncertainty': 'Unresolved'}
    value = {'schema_version': '3', 'authority': 'proposal_only', 'scientific_authority': 'not_established',
        'action': action, 'rationale': 'Synthetic future intent', 'decision_scope': decision,
        'candidate': None, 'alternatives': [], 'evidence_requests': [intent] if action == 'request_evidence' else [],
        'targets': [] if action == 'abstain' else [{'criterion': point,
            'improvement': 'Investigate this criterion', 'expected_learning': 'Whether it applies'}],
        'unresolved': [{'criterion': point, 'posture': 'unknown', 'description': 'Still unresolved'}],
        'focus_artifact': None}
    if action == 'propose_campaign':
        value['candidate'] = {'kind': 'future_campaign', 'title': 'Synthetic next campaign',
            'definition': definition, 'expected_evidence': [intent]}
    return copy.deepcopy(json.loads(json.dumps(value)))


def exchange(change=None):
    old, footprint, response, _ = predecessor_exchange()
    value = old.document().model_dump(mode='json')
    profile = checkpoint_followup_draft_schema()
    value['planning_request']['context']['output_schema'] = profile.model_dump(mode='json')
    request = CheckpointRequest.model_validate_json(json.dumps(value))
    value['planning_request_sha256'] = hashlib.sha256(encoded(request.planning_request)).hexdigest()
    request = CheckpointRequest.model_validate_json(json.dumps(value))
    original = CheckpointRequestBinding.bind(request, footprint, actor_id=request.planning_request.actor_id)
    proposed = draft(request.reference.scope.model_dump(mode='json'), request.planning_request.decision_scope)
    if change is not None:
        change(proposed, request)
    result = CheckpointFollowupDraft.model_validate_json(json.dumps(proposed))
    raw = encoded(result)
    record = response.model_dump(mode='json')
    record['request_sha256'] = original.sha256
    record['capture'].update(sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
    observed = record['observation']
    observed['attempt']['request_sha256'] = request.planning_request_sha256
    observed.update(output_sha256=hashlib.sha256(raw).hexdigest(), captured_bytes=len(raw),
        status='abstained' if result.action == 'abstain' else 'proposed')
    observed['proposal'].update(output_schema=profile.model_dump(mode='json'), payload_json=raw.decode(),
        payload_sha256=hashlib.sha256(raw).hexdigest(), action=result.action, rationale=result.rationale)
    return original, footprint, SupervisionResponse.model_validate_json(json.dumps(record)), raw
