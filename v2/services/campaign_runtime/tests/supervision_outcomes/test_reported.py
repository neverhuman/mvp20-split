"""Owner evidence binding rejects plausible but unrelated completion claims."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_campaign_runtime.supervision_outcomes import ReportedExecution
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_contracts_supervision import (
    CheckpointExecutionReport,
    CheckpointRequest,
    SupervisionResponse,
)

FIXTURES = Path(__file__).absolute().parents[4] / 'contracts/supervision/tests/fixtures'


def request():
    return CheckpointRequest.model_validate_json((FIXTURES / 'checkpoint-request.json').read_bytes())


def report(original=None, *, reason='provider_unconfigured', status='invalid'):
    original = original or request()
    data = {'reference': original.reference.model_dump(mode='json'),
        'request_sha256': hashlib.sha256(encoded(original)).hexdigest(),
        'engagement': original.planning_request.reference.model_dump(mode='json'),
        'planning_request_sha256': original.planning_request_sha256, 'stop_reason': reason, 'attempts': []}
    if reason == 'attempt_limit':
        data['attempts'] = [{'attempt': {'engagement': data['engagement'],
            'request_sha256': data['planning_request_sha256'], 'ordinal': ordinal},
            'observation_sha256': 'a' * 64, 'status': status}
            for ordinal in range(1, original.planning_request.context.limits.max_attempts + 1)]
    return data


def bind(data, original=None):
    return ReportedExecution.bind(original or request(), CheckpointExecutionReport.model_validate_json(json.dumps(data)))


def test_zero_call_and_exhausted_reports_preserve_original_bytes():
    for reason in ('provider_unconfigured', 'attempt_limit'):
        bound = bind(report(reason=reason))
        assert bound.canonical == encoded(bound.document())
        assert bound.sha256 == hashlib.sha256(bound.canonical).hexdigest()
    assert bind(report()).document().attempts == ()


@pytest.mark.parametrize('field,reason', [('reference', 'execution_report_request'),
    ('request_sha256', 'execution_report_request'), ('engagement', 'execution_report_planning'),
    ('planning_request_sha256', 'execution_report_planning'), ('ordinal', 'execution_report_attempt_identity'),
    ('count', 'execution_report_not_exhausted'), ('after_stop', 'execution_report_after_stop'),
    ('status', 'execution_report_status'), ('empty_success', 'execution_report_status')])
def test_mismatched_peer_facts_reject(field, reason):
    data = copy.deepcopy(report(reason='attempt_limit'))
    if field == 'reference':
        data['reference']['run_id'] = 'foreign'
    elif field == 'engagement':
        data['engagement']['engagement_id'] = 'foreign'
    elif field in {'request_sha256', 'planning_request_sha256'}:
        data[field] = 'f' * 64
    elif field == 'ordinal':
        data['attempts'][0]['attempt']['ordinal'] = 2
    elif field == 'count':
        data['attempts'].pop()
    elif field == 'after_stop':
        data['attempts'][0]['status'] = 'proposed'
    elif field == 'status':
        data['stop_reason'] = 'abstained'
    else:
        data['stop_reason'], data['attempts'] = 'abstained', []
    with pytest.raises(ValueError, match=reason):
        bind(data)


def test_response_requires_exact_observation_identity_and_hash():
    data = report(reason='attempt_limit')
    last = data['attempts'][-1]
    observation = {'schema_version': '2', 'attempt': last['attempt'], 'status': 'invalid',
        'reason_code': 'fixture', 'output_sha256': hashlib.sha256(b'').hexdigest(),
        'captured_bytes': 0, 'output_complete': False,
        'usage': {'input_tokens': None, 'output_tokens': None, 'accounting_units': None, 'certainty': 'unknown'},
        'proposal': None}
    response = SupervisionResponse.model_validate_json(json.dumps({'response_id': 'fixture',
        'reference': data['reference'], 'request_sha256': data['request_sha256'], 'observation': observation,
        'capture': None}))
    last['observation_sha256'] = hashlib.sha256(encoded(response.observation)).hexdigest()
    bound = bind(data)
    assert bound.require_response(response).attempt == response.observation.attempt
    with pytest.raises(ValueError, match='execution_response_request'):
        bound.require_response(response.model_copy(update={'request_sha256': 'f' * 64}))
    with pytest.raises(ValueError, match='execution_response_observation'):
        bound.require_response(response.model_copy(update={'observation': response.observation.model_copy(
            update={'reason_code': 'substituted'})}))


def test_successful_stop_still_requires_separate_response():
    data = report(reason='attempt_limit')
    data['attempts'] = data['attempts'][:1]
    data['stop_reason'] = data['attempts'][0]['status'] = 'abstained'
    bound = bind(data)
    assert bound.document().stop_reason == 'abstained'
    data['stop_reason'] = 'provider_unconfigured'
    with pytest.raises(ValueError, match='execution_report_status'):
        bind(data)
