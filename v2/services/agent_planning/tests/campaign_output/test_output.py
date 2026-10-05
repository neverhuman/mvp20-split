"""Original-request authority cannot be substituted by model output."""

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest
from amphora_agent_planning.campaign_output import CampaignOutput
from amphora_contracts_planning import campaign_draft_schema

from ..context.test_snapshot import FIXTURE as REQUEST
from ..context.test_snapshot import bind

FIXTURES = Path(__file__).parent / 'fixtures'


def output(name='future'):
    return json.loads((FIXTURES / (name + '.json')).read_bytes())


def request(name='future', **changes):
    raw = json.loads(REQUEST.read_bytes())
    raw.update(purpose='supervision' if name == 'adjustment' else 'campaign_proposal',
               decision_scope='d' * 64, runtime_cut=output('adjustment')['candidate']['cut'] if name == 'adjustment' else None)
    raw['context']['output_schema'] = campaign_draft_schema().model_dump(mode='json')
    raw['context']['allowed_actions'] = ['abstain', 'request_evidence', 'propose_campaign']
    raw.update(changes)
    return bind(raw)


def parse(raw=None, snapshot=None):
    return CampaignOutput.parse(json.dumps(output() if raw is None else raw).encode(), snapshot or request())


@pytest.mark.parametrize('name', ['future', 'adjustment', 'evidence', 'abstain'])
def test_each_shape_roundtrips_without_mutating_request_or_raw(name):
    value = output(name)
    original = copy.deepcopy(value)
    snapshot = request(name)
    before = snapshot.canonical
    parsed = parse(value, snapshot)
    assert value == original and snapshot.canonical == before
    assert CampaignOutput.parse(parsed.canonical, snapshot) == parsed
    proposal = parsed.proposal()
    assert proposal.payload_sha256 == parsed.sha256
    assert proposal.payload_json.encode() == parsed.canonical
    assert parsed.document().unresolved[0].posture == 'unknown'
    value['rationale'] = 'changed after parsing'
    assert parsed.document().rationale != value['rationale']


@pytest.mark.parametrize('case,code', [
    ('purpose', 'campaign_output_purpose'), ('profile', 'campaign_output_profile'),
    ('profile_hash', 'campaign_output_profile'), ('decision', 'campaign_decision_scope'),
    ('action', 'action_not_allowed'), ('adjustment_purpose', 'campaign_adjustment_purpose'),
    ('adjustment_cut', 'campaign_adjustment_cut'), ('cut_plan', 'campaign_adjustment_cut'),
    ('cut_frontier', 'campaign_adjustment_cut'),
])
def test_original_decision_is_authoritative(case, code):
    name = 'adjustment' if case.startswith(('adjustment', 'cut_')) else 'future'
    snapshot = request(name)
    value = output(name)
    original = snapshot.document().model_dump(mode='json')
    if case == 'purpose':
        original['purpose'] = 'knowledge_decomposition'
    elif case == 'profile':
        original['context']['output_schema']['schema_id'] = 'planning.reference-proposal'
    elif case == 'profile_hash':
        original['context']['output_schema']['sha256'] = '0' * 64
    elif case == 'decision':
        value['decision_scope'] = '0' * 64
    elif case == 'action':
        original['context']['allowed_actions'] = ['abstain']
    elif case == 'adjustment_purpose':
        original['purpose'] = 'campaign_proposal'
    elif case == 'adjustment_cut':
        value['candidate']['cut']['revision'] += 1
    elif case == 'cut_plan':
        value['candidate']['cut']['plan_sha256'] = '0' * 64
    else:
        value['candidate']['cut']['frontier_revision'] += 1
    with pytest.raises(ValueError, match=code):
        parse(value, bind(original))


@pytest.mark.parametrize('name,action,evidence,code', [
    ('future', 'abstain', False, 'campaign_abstention_payload'),
    ('evidence', 'abstain', True, 'campaign_abstention_payload'),
    ('future', 'request_evidence', False, 'campaign_evidence_payload'),
    ('abstain', 'request_evidence', False, 'campaign_evidence_payload'),
    ('abstain', 'propose_campaign', False, 'campaign_missing_candidate'),
])
def test_action_cannot_hide_payload_or_claim_an_absent_candidate(name, action, evidence, code):
    value = output(name)
    value['action'] = action
    if not evidence:
        value['evidence_requests'] = []
    with pytest.raises(ValueError, match=code):
        parse(value)


@pytest.mark.parametrize('path', [
    ('candidate', 'definition', 'scope'),
    ('candidate', 'expected_evidence', 0, 'question', 'scope'),
    ('candidate', 'expected_evidence', 0, 'needs', 0, 'scope'),
    ('candidate', 'expected_evidence', 0, 'assessments', 0, 'request', 'profile', 'scope'),
    ('candidate', 'expected_evidence', 0, 'assessments', 0, 'request', 'answers', 0, 'artifact', 'scope'),
    ('candidate', 'expected_evidence', 0, 'assessments', 0, 'request', 'receipts', 0, 'scope'),
    ('unresolved', 0, 'question', 'scope'), ('unresolved', 0, 'need', 'scope'),
])
def test_foreign_scope_is_rejected_at_every_nested_boundary(path):
    value = output()
    target = value
    for key in path:
        target = target[key]
    target['project_id'] = 'foreign'
    with pytest.raises(ValueError, match='campaign_output_scope'):
        parse(value)


@pytest.mark.parametrize('conflicting', [False, True])
def test_repeated_node_input_adjustment_is_not_independent_work(conflicting):
    value = output('adjustment')
    duplicate = copy.deepcopy(value['candidate']['changes'][0])
    if conflicting:
        duplicate['proposed']['value'] = 2.5
    value['candidate']['changes'].append(duplicate)
    with pytest.raises(ValueError, match='campaign_duplicate_adjustment'):
        parse(value, request('adjustment'))


def test_same_node_input_in_distinct_authored_scope_is_a_distinct_proposal():
    value = output('adjustment')
    duplicate = copy.deepcopy(value['candidate']['changes'][0])
    duplicate['target']['scope_path'] = ['nested']
    value['candidate']['changes'].append(duplicate)
    assert len(parse(value, request('adjustment')).document().candidate.changes) == 2


@pytest.mark.parametrize('raw', [b'', b' ' * 65537, b'\xff', b'[]', b'{',
    b'{"action":"abstain","action":"propose_campaign"}', b'{"rationale":NaN}',
    b'{"rationale":Infinity}', b'{"rationale":1e9999}', b'[' * 2000 + b']' * 2000,
    b'{"unresolved":[{"posture":"weak","posture":"unknown"}]}'], ids=['empty', 'oversize', 'utf8', 'array', 'syntax', 'duplicate', 'nan', 'infinity', 'overflow', 'deep', 'nested_duplicate'])
def test_malformed_bounded_json_fails_closed(raw):
    with pytest.raises(ValueError):
        CampaignOutput.parse(raw, request())


def test_surrogate_text_and_nonbytes_are_not_valid_utf8_output():
    value = output()
    value['rationale'] = '\ud800'
    with pytest.raises(ValueError):
        parse(value)
    with pytest.raises(ValueError, match='typed_output_size'):
        CampaignOutput.parse(json.dumps(output()), request())


def test_canonical_size_can_exceed_small_input_via_default_fields():
    value = output('adjustment')
    change = value['candidate']['changes'][0]
    del change['proposed']['unit']
    value['candidate']['changes'] = [dict(copy.deepcopy(change), input_name='input-' + str(i)) for i in range(64)]
    value['candidate']['expected_evidence'] = []
    value['unresolved'] = [dict(value['unresolved'][0], description='x') for _ in range(64)]
    def encode():
        return json.dumps(value, separators=(',', ':')).encode()
    for item in value['unresolved']:
        item['description'] += 'x' * min(2047, 65536 - len(encode()))
    raw = encode()
    assert len(raw) == 65536
    # The omitted public scalar unit defaults increase canonical bytes.
    with pytest.raises(ValueError, match='typed_output_size'):
        CampaignOutput.parse(raw, request('adjustment'))


def test_direct_value_construction_and_noncanonical_bytes_rebind_on_projection():
    parsed = parse()
    with pytest.raises(ValueError, match='campaign_output_binding'):
        replace(parsed, canonical=parsed.canonical + b' ').proposal()
    raw = parsed.document().model_dump(mode='json')
    raw['decision_scope'] = '0' * 64
    with pytest.raises(ValueError, match='campaign_decision_scope'):
        replace(parsed, canonical=json.dumps(raw).encode()).proposal()


def test_uncertainty_is_preserved_without_global_quality_veto():
    value = output('abstain')
    value['unresolved'] = [dict(value['unresolved'][0], posture=posture)
                           for posture in ('unknown', 'weak', 'contradictory', 'missing', 'inapplicable')]
    value['alternatives'] = output()['alternatives']
    parsed = parse(value)
    assert len(parsed.document().unresolved) == 5
    assert len(parsed.document().alternatives) == 1
