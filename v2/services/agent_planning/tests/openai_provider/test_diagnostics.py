"""Closed diagnostics cannot retain free-form provider text or change outcomes."""
import hashlib
import json

import pytest
from amphora_agent_planning.openai_provider.diagnostics import ResponseDiagnostic


@pytest.mark.parametrize('status', ['failed', 'incomplete', 'completed'])
def test_classification_and_digest_without_remote_prose(status):
    value = {'status': status, 'error': {'code': 'server_error', 'message': 'secret-marker'},
             'incomplete_details': {'reason': 'max_output_tokens'},
             'output': [{'content': [{'type': 'refusal', 'refusal': 'secret-marker'}]}]}
    raw = json.dumps(value).encode()
    result = ResponseDiagnostic.capture(raw, value).document()
    assert result['status'] == status and result['error_code'] == 'server_error'
    assert result['incomplete_reason'] == 'max_output_tokens' and result['refused']
    assert result['response_sha256'] == hashlib.sha256(raw).hexdigest()
    assert result['response_bytes'] == len(raw)
    assert 'secret-marker' not in json.dumps(result)


@pytest.mark.parametrize('unknown', ['secret-marker', {}, [], 12, True])
def test_arbitrary_values_never_escape(unknown):
    value = {'status': unknown, 'error': {'code': unknown}, 'incomplete_details': {'reason': unknown}, 'output': unknown}
    result = ResponseDiagnostic.capture(b'{}', value).document()
    assert result['status'] == result['error_code'] == result['incomplete_reason'] == 'unclassified'
    assert result['refused'] is False
    assert 'secret-marker' not in json.dumps(result)
