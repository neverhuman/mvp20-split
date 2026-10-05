"""Candidate shapes preserve scientific uncertainty without granting acceptance."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_planning import CampaignDraft, campaign_draft_schema
from jsonschema import Draft202012Validator
from pydantic import ValidationError

FIXTURES = Path(__file__).parent / 'fixtures'


def fixture(name):
    return json.loads((FIXTURES / (name + '.json')).read_bytes())


@pytest.mark.parametrize('name', ['abstain', 'evidence', 'future', 'adjustment'])
def test_public_candidates_roundtrip_and_portable_schema(name):
    value = fixture(name)
    parsed = CampaignDraft.model_validate_json(json.dumps(value))
    Draft202012Validator(CampaignDraft.model_json_schema()).validate(value)
    assert CampaignDraft.model_validate_json(parsed.model_dump_json()) == parsed
    assert parsed.authority == 'proposal_only'
    assert parsed.scientific_authority == 'not_established'
    assert parsed.unresolved[0].posture == 'unknown'
    assert isinstance(parsed.unresolved, tuple)
    with pytest.raises(ValidationError):
        parsed.action = 'abstain'


@pytest.mark.parametrize('key,value', [
    ('schema_version', '2'), ('authority', 'accepted'),
    ('scientific_authority', 'validated'), ('handler', 'run()'),
    ('accepted_answer', {}), ('action', 'execute'), ('decision_scope', 'latest'),
    ('rationale', ''), ('rationale', 'x' * 4097),
])
def test_closed_output_envelope(key, value):
    raw = fixture('future')
    raw[key] = value
    with pytest.raises(ValidationError):
        CampaignDraft.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize('case', ['kind', 'handler', 'definition', 'title', 'empty_changes',
                                 'too_many_changes', 'scope_path', 'cut_bool', 'missing_previous'])
def test_closed_candidate_boundary(case):
    raw = fixture('future' if case in ('kind', 'handler', 'definition', 'title') else 'adjustment')
    candidate = raw['candidate']
    if case == 'kind':
        candidate['kind'] = 'execute_python'
    elif case == 'handler':
        candidate['definition']['body']['nodes'][0]['handler'] = 'arbitrary()'
    elif case == 'definition':
        del candidate['definition']
    elif case == 'title':
        candidate['title'] = 'x' * 129
    elif case == 'empty_changes':
        candidate['changes'] = []
    elif case == 'too_many_changes':
        candidate['changes'] *= 65
    elif case == 'scope_path':
        candidate['changes'][0]['target']['scope_path'] = ['nested'] * 17
    elif case == 'cut_bool':
        candidate['cut']['revision'] = True
    else:
        del candidate['changes'][0]['previous_value_sha256']
    with pytest.raises(ValidationError):
        CampaignDraft.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize('kind,value', [('integer', True), ('integer', 1.5),
    ('integer', 9007199254740992), ('number', '1.25'), ('number', 1e101),
    ('number', float('inf')), ('number', float('nan')), ('boolean', 1), ('string', 1)])
def test_reuses_strict_finite_scalar_contract(kind, value):
    raw = fixture('adjustment')
    raw['candidate']['changes'][0]['proposed'] = {'kind': kind, 'value': value}
    with pytest.raises(ValidationError):
        CampaignDraft.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize('field,maximum', [('evidence_requests', 64), ('alternatives', 16), ('unresolved', 64)])
def test_top_level_collections_are_bounded(field, maximum):
    raw = fixture('evidence' if field == 'evidence_requests' else 'future')
    raw[field] *= maximum + 1
    with pytest.raises(ValidationError):
        CampaignDraft.model_validate_json(json.dumps(raw))


def test_schema_pin_is_exact_published_validation_encoding():
    schema = CampaignDraft.model_json_schema(mode='validation')
    schema.update({'$schema': 'https://json-schema.org/draft/2020-12/schema',
                   '$id': 'urn:amphora:planning.campaign-draft:1:validation'})
    raw = (json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False) + '\n').encode('utf-8')
    reference = campaign_draft_schema()
    assert reference.schema_id == 'planning.campaign-draft'
    assert reference.version == '1'
    assert reference.sha256 == hashlib.sha256(raw).hexdigest()


def test_wire_shape_does_not_claim_request_binding_or_action_policy():
    raw = fixture('future')
    raw.update(action='abstain', decision_scope='f' * 64)
    # Structural acceptance is deliberately weaker than the owning parser/policy.
    assert CampaignDraft.model_validate_json(json.dumps(raw)).candidate is not None
