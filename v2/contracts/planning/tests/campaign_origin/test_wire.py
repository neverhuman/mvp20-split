"""Public origin shape is bounded and additive; owner policy checks relations."""

import json
from pathlib import Path

import pytest
from amphora_contracts_planning import CampaignOrigin, CampaignOriginV2, EngagementRequest
from pydantic import ValidationError


def document():
    request = EngagementRequest.model_validate_json(
        (Path(__file__).parents[1] / 'fixtures/request.json').read_bytes())
    scope = request.reference.scope.model_dump(mode='json')
    digest = 'a' * 64
    return {'schema_version': '1', 'origin_sha256': digest, 'origin': {
        'schema_version': '1', 'authority': 'historical_compiler_provenance',
        'draft': {'scope': scope, 'draft_id': 'draft', 'revision': 1, 'content_sha256': digest},
        'proposal': {'actor_id': request.actor_id,
            'attempt': {'engagement': request.reference.model_dump(mode='json'), 'request_sha256': digest, 'ordinal': 1},
            'preparation_sha256': digest, 'prepared_proposal_sha256': digest, 'output_sha256': digest,
            'action': 'propose_campaign', 'rationale': 'Recorded rationale',
            'context': request.context.model_dump(mode='json'),
            'usage': {'input_tokens': None, 'output_tokens': None, 'accounting_units': None, 'certainty': 'unknown'},
            'capture_publication': 'not_published'},
        'save': {'owner_id': 'runtime', 'selection_id': 'selection', 'selection_sha256': digest,
            'effect_id': 'effect', 'effect_sha256': digest, 'readback_sha256': digest,
            'receipt': {'schema_version': '1', 'outcome': {'status': 'accepted',
                'binding': {'identity': {'scope': scope, 'actor_id': 'compiler',
                    'command_family': 'definition.save', 'command_id': 'save'},
                    'request_sha256': digest, 'operation_id': 'operation'},
                'committed': {'kind': 'draft_revision', 'object_id': 'draft', 'revision': 1, 'content_sha256': digest}}}},
        'research': {'selection': None, 'records': []}, 'tools': [], 'limitations': ['historical_only']}}


def test_roundtrip_and_unknown_usage():
    value = CampaignOrigin.model_validate_json(json.dumps(document()))
    assert CampaignOrigin.model_validate_json(value.model_dump_json()) == value
    assert value.origin.proposal.usage.accounting_units is None


def test_v2_knowledge_is_explicit_and_v1_stays_closed():
    raw = document()
    raw['schema_version'] = raw['origin']['schema_version'] = '2'
    raw['origin']['knowledge'] = None
    value = CampaignOriginV2.model_validate_json(json.dumps(raw))
    assert value.origin.knowledge is None
    with pytest.raises(ValidationError):
        CampaignOrigin.model_validate_json(json.dumps(raw))
    del raw['origin']['knowledge']
    with pytest.raises(ValidationError):
        CampaignOriginV2.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize('path,value', [
    (('schema_version',), '2'), (('origin', 'authority'), 'execution_acceptance'),
    (('origin', 'draft', 'revision'), True), (('origin', 'draft', 'revision'), 0),
    (('origin', 'proposal', 'rationale'), 'a' * 4097),
    (('origin', 'proposal', 'api_key'), 'forbidden'),
    (('origin', 'proposal', 'capture_publication'), 'published'),
    (('origin', 'research', 'records'), [None] * 161),
    (('origin', 'limitations'), []),
])
def test_strict_projection_boundary(path, value):
    raw = document()
    target = raw
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        CampaignOrigin.model_validate_json(json.dumps(raw))
