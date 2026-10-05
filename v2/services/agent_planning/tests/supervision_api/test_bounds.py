"""Streaming probes retain the middleware boundary and explicit whole-body timeout."""

import asyncio

import pytest
from amphora_agent_planning.supervision_api.bounds import RequestBounds


def probe(messages, *, slow=False, kind='http'):
    sent, calls = [], []
    async def receive():
        if slow:
            await asyncio.sleep(0.1)
        return messages.pop(0)
    async def send(value):
        sent.append(value)
    async def app(scope, receive, send):
        calls.append(scope['type'])
        if scope['type'] == 'http':
            calls.append(await receive())
    asyncio.run(RequestBounds(app, max_bytes=32, timeout=0.02)({'type': kind}, receive, send))
    return sent, calls


def test_chunked_body_is_replayed_once_and_disconnect_is_not_a_request():
    _, calls = probe([{'type': 'http.request', 'body': b'{', 'more_body': True},
                      {'type': 'http.request', 'body': b'}', 'more_body': False}])
    assert calls == ['http', {'type': 'http.request', 'body': b'{}', 'more_body': False}]
    assert probe([{'type': 'http.disconnect'}]) == ([], [])
    assert probe([], kind='lifespan')[1] == ['lifespan']


def test_trickled_body_and_cumulative_bytes_are_bounded():
    sent, calls = probe([{'type': 'http.request', 'body': b'{}'}], slow=True)
    assert sent[0]['status'] == 408 and not calls
    sent, calls = probe([{'type': 'http.request', 'body': b' ' * 20, 'more_body': True},
                         {'type': 'http.request', 'body': b' ' * 20}])
    assert sent[0]['status'] == 413 and not calls


def test_invalid_bounds_are_rejected():
    with pytest.raises(ValueError, match='invalid_request_bounds'):
        RequestBounds(None, timeout=11)
