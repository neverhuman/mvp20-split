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


@pytest.mark.parametrize('status', [200, 400])
@pytest.mark.parametrize('request_id', ['req_0123', 'e1f501fc-d97c-446b-9b20-674a6180837b', 'sk-secret-marker', 'bad\nheader', None])
def test_http_request_correlation_excludes_credentials_and_arbitrary_headers(status, request_id):
    from amphora_agent_planning.openai_provider.http import OpenAIHTTP
    from amphora_agent_planning.providers.port import ProviderUnavailable
    from .test_adapter import Connection
    connection = Connection(status, b'{}')
    connection.getheader = lambda name: request_id if name == 'x-request-id' else 'secret-marker'
    transport = OpenAIHTTP('secret-marker', connection_factory=lambda *_a, **_k: connection)
    if status == 200: assert transport.send(b'{}') == b'{}'
    else:
        with pytest.raises(ProviderUnavailable): transport.send(b'{}')
    evidence = transport.last_exchange
    assert evidence['http_status'] == status
    assert evidence['request_id'] == (request_id if request_id in ('req_0123', 'e1f501fc-d97c-446b-9b20-674a6180837b') else None)
    assert evidence['request_body_sha256'] == hashlib.sha256(b'{}').hexdigest()
    assert 'secret-marker' not in json.dumps(evidence)
    assert evidence['endpoint'] == 'https://api.openai.com/v1/responses'


@pytest.mark.parametrize('usage', [None, {}, {'input_tokens': 0, 'output_tokens': 0}])
def test_shape_distinguishes_absent_usage_and_empty_output_without_text(usage):
    value = {'output': [{'type': 'reasoning', 'summary': 'secret-marker'},
                        {'type': 'message', 'content': [{'type': 'output_text', 'text': 'secret-marker'}]},
                        {'type': 'secret-marker'}, None], 'usage': usage}
    result = ResponseDiagnostic.capture(b'{}', value).document()
    shape = result['shape']
    assert (shape['message_items'], shape['reasoning_items'], shape['other_items']) == (1, 1, 2)
    assert shape['output_text_blocks'] == 1 and shape['output_text_bytes'] == 13
    assert shape['usage_present'] is (usage is not None)
    assert shape['input_tokens_present'] is (usage is not None and 'input_tokens' in usage)
    assert shape['output_tokens_present'] is (usage is not None and 'output_tokens' in usage)
    assert 'secret-marker' not in json.dumps(result)
