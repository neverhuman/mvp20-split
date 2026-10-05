"""Exact restart origins and tampered historical bytes."""

import base64
import json

import pytest
from amphora_campaign_runtime.supervision_journal import RequestFrame

from ..supervision_requests.test_binding import footprint, original


def frame():
    return RequestFrame.capture(original(), footprint(), prepared_by='runtime-supervisor',
                                planning_actor=original().planning_request.actor_id)


def raw(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def test_original_reconstructed_without_current_nodes():
    first = frame()
    restored = RequestFrame.from_bytes(first.canonical)
    assert restored == first
    assert restored.footprint() == footprint()
    assert restored.request == original()
    assert restored.sha256 != restored.request_sha256
    assert restored.document().prepared_by == 'runtime-supervisor'


@pytest.mark.parametrize('change', ['state', 'outputs', 'view', 'request', 'profile', 'base64', 'extra'])
def test_tampered_origin_rejected(change):
    document = json.loads(frame().canonical)
    if change in {'state', 'outputs'}:
        document['observations'][0][change] = base64.b64encode(b'{"changed":true}').decode()
    elif change == 'view':
        document['observations'][0]['node']['activation_id'] = 'f' * 64
    elif change == 'request':
        document['request']['planning_request_sha256'] = 'f' * 64
    elif change == 'profile':
        document['profile'] = 'runtime-supervision-request-frame.v2'
    elif change == 'base64':
        document['observations'][0]['state'] = 'bnVsbA==\n'
    else:
        document['extra'] = True
    with pytest.raises(ValueError):
        RequestFrame.from_bytes(raw(document))


@pytest.mark.parametrize('kind', ['whitespace', 'duplicate', 'mutable', 'oversize', 'nonfinite'])
def test_noncanonical_or_unbounded_frames_rejected(kind):
    value = frame().canonical
    if kind == 'whitespace':
        value += b'\n'
    elif kind == 'duplicate':
        value = b'{"prepared_by":"other",' + value[1:]
    elif kind == 'mutable':
        value = bytearray(value)
    elif kind == 'oversize':
        value = b' ' * 16777217
    else:
        value = value.replace(b'"deadline_unix_ms":', b'"nonfinite":NaN,"deadline_unix_ms":')
    with pytest.raises(ValueError):
        RequestFrame.from_bytes(value)


def test_configured_planning_actor_is_checked_at_capture():
    with pytest.raises(ValueError, match='planning_actor_mismatch'):
        RequestFrame.capture(original(), footprint(), prepared_by='runtime', planning_actor='other')
