"""Criterion targeting shapes preserve old proposal/preparation interpretation."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_planning import (
    CampaignDraft,
    CampaignFollowupSelection,
    CampaignResearchSelection,
    CheckpointDraft,
    CheckpointFollowupDraft,
    campaign_followup_selection_schema,
    checkpoint_followup_draft_schema,
)
from pydantic import ValidationError

ROOT = Path(__file__).absolute().parents[4]
FIXTURE = Path(__file__).absolute().parents[1] / 'fixtures/campaign-research-selection.json'


def selection():
    value = json.loads(FIXTURE.read_bytes())
    value.update(schema_version='2', focus_artifact=None, criteria=[{
        'question': value['questions'][0], 'need': value['needs'][0],
        'criterion_id': 'applicability', 'assessment': value['assessments'][0]}])
    return value


def draft():
    criterion = selection()['criteria'][0]
    return {'schema_version': '3', 'authority': 'proposal_only', 'scientific_authority': 'not_established',
            'action': 'request_evidence', 'rationale': 'Resolve the selected disagreement',
            'decision_scope': 'a' * 64, 'candidate': None, 'evidence_requests': [], 'alternatives': [],
            'targets': [{'criterion': criterion, 'improvement': 'Test applicability',
                         'expected_learning': 'Which observations apply to this context'}],
            'unresolved': [{'criterion': criterion, 'posture': 'contradictory',
                            'description': 'The selected point remains unresolved'}], 'focus_artifact': None}


def test_exact_criterion_and_unresolved_identity_survive_roundtrip():
    output = CheckpointFollowupDraft.model_validate_json(json.dumps(draft()))
    selected = CampaignFollowupSelection.model_validate_json(json.dumps(selection()))
    assert output.targets[0].criterion == selected.criteria[0] == output.unresolved[0].criterion
    assert CheckpointFollowupDraft.model_validate_json(output.model_dump_json()) == output
    assert CampaignFollowupSelection.model_validate_json(selected.model_dump_json()) == selected
    assert type(output.targets) is tuple and type(selected.criteria) is tuple
    with pytest.raises(ValidationError):
        output.targets = ()


def test_predecessors_do_not_silently_accept_new_profile():
    for record in (CampaignDraft, CheckpointDraft):
        with pytest.raises(ValidationError):
            record.model_validate_json(json.dumps(draft()))
    with pytest.raises(ValidationError):
        CampaignResearchSelection.model_validate_json(json.dumps(selection()))
    old = json.loads(FIXTURE.read_bytes())
    with pytest.raises(ValidationError):
        CampaignFollowupSelection.model_validate_json(json.dumps(old))


@pytest.mark.parametrize('case', ['authority', 'science', 'version', 'extra', 'resolved', 'revision_bool',
                                  'criterion', 'improvement', 'learning', 'targets_limit', 'unresolved_limit', 'adjustment'])
def test_closed_future_only_output_and_limits(case):
    value = draft()
    if case == 'authority': value['authority'] = 'accepted'
    elif case == 'science': value['scientific_authority'] = 'established'
    elif case == 'version': value['schema_version'] = '2'
    elif case == 'extra': value['execute_now'] = True
    elif case == 'resolved': value['unresolved'][0]['posture'] = 'resolved'
    elif case == 'revision_bool': value['targets'][0]['criterion']['question']['revision'] = True
    elif case == 'criterion': value['targets'][0]['criterion']['criterion_id'] = ''
    elif case == 'improvement': value['targets'][0]['improvement'] = ''
    elif case == 'learning': value['targets'][0]['expected_learning'] = 'x' * 2049
    elif case == 'targets_limit': value['targets'] *= 33
    elif case == 'unresolved_limit': value['unresolved'] *= 65
    else: value['candidate'] = {'kind': 'materialization_adjustment'}
    with pytest.raises(ValidationError):
        CheckpointFollowupDraft.model_validate_json(json.dumps(value))


def test_preparation_limits_and_optional_unassessed_point():
    value = selection()
    value['criteria'][0]['assessment'] = None
    assert CampaignFollowupSelection.model_validate_json(json.dumps(value)).criteria[0].assessment is None
    value['criteria'] *= 65
    with pytest.raises(ValidationError):
        CampaignFollowupSelection.model_validate_json(json.dumps(value))


def test_shape_validation_is_not_membership_or_duplicate_authority():
    value = draft()
    value['targets'][0]['criterion']['question']['scope']['project_id'] = 'different'
    value['targets'].append(copy.deepcopy(value['targets'][0]))
    # C2 owner domain validation must reject these; DTOs cannot resolve owner records.
    assert len(CheckpointFollowupDraft.model_validate_json(json.dumps(value)).targets) == 2


def test_profile_digests_and_all_predecessor_bytes_are_pinned():
    schemas = ROOT / 'contracts/schemas'
    pins = json.loads((Path(__file__).parent / 'predecessor_schema_pins.json').read_bytes())
    for name, digest in pins['schemas'].items():
        assert hashlib.sha256((schemas / name).read_bytes()).hexdigest() == digest, name
    for profile in (campaign_followup_selection_schema(), checkpoint_followup_draft_schema()):
        assert profile.version == '1'
        raw = (schemas / 'v1' / (profile.schema_id + '.validation.json')).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == profile.sha256
