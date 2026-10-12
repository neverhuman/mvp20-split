import pytest
from amphora_agent_planning.curation_declaration.workflow import DeclarationTransport
from amphora_agent_planning.publication.transport import PublicationTransport
from amphora_tool_protocol import ProtocolError
from ..publication.test_transport import peer as peer


def test_declaration_text_upload_uses_closed_authenticated_transport(peer):
    server, endpoint = peer
    body = b'{"format":"planning-campaign-decision.v2"}'
    with pytest.raises(ProtocolError, match='publication_media_type'):
        PublicationTransport(endpoint, 't' * 32).request('PUT', '/v1/uploads/u/content', body, media_type='text/plain')
    assert server.calls == []
    result = DeclarationTransport(endpoint, 't' * 32).request('PUT', '/v1/uploads/u/content', body, media_type='text/plain')
    assert result.status == 200
    assert server.calls == [('PUT', '/v1/uploads/u/content', 'Bearer ' + 't' * 32, body)]
    with pytest.raises(ProtocolError, match='publication_path'):
        DeclarationTransport(endpoint, 't' * 32).request('POST', '/v1/sources', b'{}')
