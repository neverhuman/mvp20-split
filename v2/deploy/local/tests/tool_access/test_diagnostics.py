from concurrent.futures import ThreadPoolExecutor

import pytest
from amphora_deployment.tool_access.diagnostics import TransportDiagnostics


def test_fixed_categories_concurrent_counts_and_detached_snapshot():
    diagnostics = TransportDiagnostics()
    def record(_):
        diagnostics.failure('response_headers', 'timeout')
        diagnostics.response(502)
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(record, range(100)))
    snapshot = diagnostics.snapshot()
    assert snapshot == {'failures': {'response_headers.timeout': 100}, 'responses': {'5xx': 100}}
    snapshot['failures'].clear()
    assert diagnostics.snapshot()['failures'] == {'response_headers.timeout': 100}


@pytest.mark.parametrize('stage,kind', [('private-header', 'io'), ('request', 'secret-exception')])
def test_arbitrary_diagnostics_never_retained(stage, kind):
    diagnostics = TransportDiagnostics()
    with pytest.raises(ValueError, match='^tool_tls_diagnostic_category$'):
        diagnostics.failure(stage, kind)
    assert diagnostics.snapshot() == {'failures': {}, 'responses': {}}


@pytest.mark.parametrize('status', [True, 99, 600, 'private-body'])
def test_invalid_status_never_retained(status):
    with pytest.raises(ValueError, match='^tool_tls_diagnostic_status$'):
        TransportDiagnostics().response(status)
