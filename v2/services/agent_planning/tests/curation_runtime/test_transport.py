import pytest
from amphora_contracts_graph_runtime import DraftRevision
from amphora_agent_planning.metadata_reads import MetadataTransport, MetadataWindow
from amphora_agent_planning.metadata_reads.targets import target
from ..metadata_reads.test_transport import server
from .test_context import case


def test_exact_draft_route_uses_existing_authenticated_bounded_http(server):
    host, _ = server
    _, _, draft, _ = case()
    host.body = draft.model_dump_json().encode()
    transport = MetadataTransport('runtime', f'http://127.0.0.1:{host.server_port}', 'r' * 32)
    path = '/v1/definition-drafts/original?revision=1'
    assert target('runtime', path) is DraftRevision
    assert transport.read(path, MetadataWindow('runtime')) == draft
    assert host.calls == [(path, 'Bearer ' + 'r' * 32)]


@pytest.mark.parametrize('query', ['', '?revision=0', '?revision=-1', '?revision=01',
    '?revision=1&revision=2', '?revision=9007199254740992', '?revision=1&latest=true'])
def test_unpinned_or_ambiguous_draft_routes_reject_before_contact(query):
    with pytest.raises(ValueError): target('runtime', '/v1/definition-drafts/original' + query)
