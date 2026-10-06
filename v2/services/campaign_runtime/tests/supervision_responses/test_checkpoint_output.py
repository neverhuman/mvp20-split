"""Exact new-profile capture through Runtime request and response boundaries."""

import hashlib
import json

import pytest
from amphora_campaign_runtime.supervision_requests.binding import (
    CheckpointRequestBinding,
    encoded,
)
from amphora_campaign_runtime.supervision_responses import SupervisionResponseBinding
from amphora_contracts_planning import CheckpointDraft, checkpoint_draft_schema
from amphora_contracts_supervision import CheckpointRequest, SupervisionResponse

from ..supervision_journal.test_checkpoint_frames import frame
from .support import FIXTURES, response


def exchange(*, alteration=None, original=None):
    original = original or frame()
    data = original.request.model_dump(mode='json')
    data['planning_request']['context']['output_schema'] = checkpoint_draft_schema().model_dump(mode='json')
    request = CheckpointRequest.model_validate_json(json.dumps(data))
    data['planning_request_sha256'] = hashlib.sha256(encoded(request.planning_request)).hexdigest()
    request = CheckpointRequest.model_validate_json(json.dumps(data))
    bound = CheckpointRequestBinding.bind(request, original.footprint(), actor_id=request.planning_request.actor_id)
    draft = json.loads((FIXTURES / 'capture-adjustment.json').read_bytes())
    target = request.snapshot.reads[0].node.path
    draft.update(schema_version='2', decision_scope=request.planning_request.decision_scope)
    draft['unresolved'] = []
    draft['evidence_requests'] = []
    draft['candidate']['expected_evidence'] = []
    draft['candidate'].update(kind='materialization_adjustment', checkpoint_seed_sha256='b' * 64,
        cut=request.snapshot.cut.model_dump(mode='json'), changes=[{'target': target.model_dump(mode='json'),
            'field_name': 'temperature', 'previous_value_sha256': 'c' * 64,
            'proposed': {'kind': 'number', 'value': '0.1234567890123456789'}}])
    if alteration == 'duplicate':
        draft['candidate']['changes'] *= 2
    elif alteration == 'cut':
        draft['candidate']['cut']['revision'] += 1
    draft = CheckpointDraft.model_validate_json(json.dumps(draft))
    raw = encoded(draft)
    old, _ = response('adjustment')
    document = old.model_dump(mode='json')
    document.update(reference=request.reference.model_dump(mode='json'), request_sha256=bound.sha256)
    document['capture'].update(scope=request.reference.scope.model_dump(mode='json'),
        sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
    observation = document['observation']
    observation['attempt'].update(engagement=request.planning_request.reference.model_dump(mode='json'),
        request_sha256=request.planning_request_sha256)
    observation.update(output_sha256=hashlib.sha256(raw).hexdigest(), captured_bytes=len(raw))
    observation['proposal'].update(output_schema=checkpoint_draft_schema().model_dump(mode='json'),
        payload_json=raw.decode(), payload_sha256=hashlib.sha256(raw).hexdigest(),
        action=draft.action, rationale=draft.rationale)
    return bound, original.footprint(), SupervisionResponse.model_validate_json(json.dumps(document)), raw


def test_checkpoint_capture_retains_exact_decimal_without_accepting_effect():
    original, footprint, record, raw = exchange()
    bound = SupervisionResponseBinding.bind(original, footprint, record,
        actor_id=original.document().planning_request.actor_id, capture_bytes=raw)
    assert bound.document() == record
    assert b'0.1234567890123456789' in bound.canonical
    assert 'outcome' not in type(bound.document()).model_fields


@pytest.mark.parametrize('case,reason', [('duplicate', 'duplicate_adjustment'), ('cut', 'adjustment_cut_mismatch')])
def test_new_profile_still_checks_exact_cut_and_duplicate_fields(case, reason):
    original, footprint, record, raw = exchange(alteration=case)
    with pytest.raises(ValueError, match=reason):
        SupervisionResponseBinding.bind(original, footprint, record,
            actor_id=original.document().planning_request.actor_id, capture_bytes=raw)
