import time

import pytest
from amphora_agent_planning.knowledge_access import KnowledgeReadWindow
from amphora_agent_planning.research_access import ResearchReadWindow, ResearchTransport

from ..knowledge_access.test_transport import peer  # noqa: F401
from ..research_proposals.support import ResearchCase


@pytest.fixture
def research_peer(peer):  # noqa: F811
    server, _, _ = peer
    case = ResearchCase()
    question = case.known_question()
    server.body = question.model_dump_json().encode()
    transport = ResearchTransport(f'http://127.0.0.1:{server.server_port}', 't' * 32)
    return server, transport, question


def test_authenticated_question_read_uses_distinct_closed_route_and_window(research_peer):
    server, transport, question = research_peer
    window = ResearchReadWindow()
    assert transport.read('/v1/questions/read', question.reference, window) == question
    assert server.calls == [('/v1/questions/read', 'Bearer ' + 't' * 32, question.reference.model_dump(mode='json'))]
    assert window.calls == 1 and window.consumed == len(server.body)
    with pytest.raises(ValueError, match='research_peer_path'):
        transport.read('/v1/graph-profiles/read', question.reference, window)
    with pytest.raises(ValueError, match='research_read_profile_mismatch'):
        transport.read('/v1/questions/read', question.reference, KnowledgeReadWindow())
    assert len(server.calls) == 1


@pytest.mark.parametrize('status,reason', [(403, 'research_access_denied'), (404, 'research_reference_unavailable'),
                                        (503, 'research_peer_unavailable')])
def test_research_status_is_explicit_without_reflecting_peer_body(research_peer, status, reason):
    server, transport, question = research_peer
    server.status, server.body = status, b'SECRET peer body'
    with pytest.raises(ValueError, match='^' + reason + '$'):
        transport.read('/v1/questions/read', question.reference, ResearchReadWindow())


def test_bad_json_and_response_overflow_are_not_question_records(research_peer):
    server, transport, question = research_peer
    server.body = b'{"duplicate":1,"duplicate":2}'
    with pytest.raises(ValueError, match='research_peer_protocol'):
        transport.read('/v1/questions/read', question.reference, ResearchReadWindow())
    server.body = b'x' * 1048577
    with pytest.raises(ValueError, match='research_response_limit'):
        transport.read('/v1/questions/read', question.reference, ResearchReadWindow())


@pytest.mark.parametrize('kind', ['trickle', 'trickle_headers'])
def test_shared_wall_clock_bound_applies_to_research(research_peer, kind):
    server, transport, question = research_peer
    setattr(server, kind, True)
    start = time.monotonic()
    with pytest.raises(ValueError, match='research_(read_expired|peer_unavailable)'):
        transport.read('/v1/questions/read', question.reference, ResearchReadWindow(seconds=0.12))
    assert time.monotonic() - start < 1


def test_profile_is_immutable_and_aggregate_caps_are_enforced():
    window = ResearchReadWindow()
    with pytest.raises(TypeError):
        window.profile.routes['/v1/questions/write'] = window.profile.routes['/v1/questions/read']
    for _ in range(64):
        window.start()
    with pytest.raises(ValueError, match='research_read_call_limit'):
        window.start()
    with pytest.raises(ValueError, match='research_read_byte_limit'):
        window.consume(4194305)
    with pytest.raises(ValueError, match='research_read_deadline'):
        ResearchReadWindow(seconds=16)
