"""Retained v2 frames bind exact targets without reinterpreting old journals."""

import base64
import json
from pathlib import Path

import pytest
from amphora_campaign_runtime.supervision_journal.checkpoint_frames import (
    CheckpointFrame,
    read_frame,
)
from amphora_campaign_runtime.supervision_journal.frames import RequestFrame
from amphora_campaign_runtime.supervision_journal.series import RequestSeries
from amphora_campaign_runtime.supervision_requests.binding import (
    CheckpointRequestBinding,
)
from amphora_campaign_runtime.supervision_requests.projection import CheckpointExport
from amphora_contracts_supervision import CheckpointRequest
from pydantic import ValidationError

FIXTURES = Path(__file__).parent / 'fixtures'


def frame():
    return CheckpointFrame.from_bytes((FIXTURES / 'checkpoint-frame.json').read_bytes())


def test_exact_frame_rebuild_and_owned_bytes():
    original = frame()
    request = original.request
    rebuilt = CheckpointFrame.capture(request, original.footprint(), prepared_by='runtime-fixture',
                                      planning_actor='fixture')
    assert rebuilt.canonical == original.canonical and rebuilt.sha256 == original.sha256
    assert rebuilt.request_sha256 == original.request_sha256
    bound = CheckpointRequestBinding.bind(request, original.footprint(), actor_id='fixture')
    assert bound.document() == request
    assert CheckpointExport(original.footprint()).document() == request.snapshot
    assert original.document().profile == 'runtime-supervision-request-frame.v2'
    assert read_frame(original.canonical) == original
    assert RequestSeries((original,)).frames == (original,)
    with pytest.raises(ValidationError):
        RequestFrame.from_bytes(original.canonical)


@pytest.mark.parametrize('change,reason', [
    ('fields', 'scope_snapshot_mismatch'),
    ('state', 'scope_snapshot_mismatch'),
    ('status', 'target_unavailable'),
    ('kind', 'checkpoint_target_mismatch'),
    ('duplicate', 'duplicate_checkpoint_field'),
])
def test_tampered_frame_cannot_be_recovered_as_original(change, reason):
    doc = json.loads(frame().canonical)
    if change == 'fields':
        doc['request']['snapshot']['checkpoints'][0]['fields'] = ['pressure']
    elif change == 'state':
        doc['observations'][0]['state'] = base64.b64encode(b'{"changed":true}').decode()
    elif change == 'status':
        doc['observations'][0]['node']['status'] = 'issued'
    elif change == 'kind':
        doc['observations'][0]['node']['kind'] = 'invoke'
    else:
        doc['request']['snapshot']['checkpoints'][0]['fields'] *= 2
    with pytest.raises(ValueError, match=reason):
        CheckpointFrame(json.dumps(doc, sort_keys=True, separators=(',', ':')).encode())


def test_noncanonical_bytes_and_legacy_export_reject():
    original = frame()
    with pytest.raises(ValueError, match='noncanonical_frame'):
        CheckpointFrame(original.canonical + b' ')
    with pytest.raises(ValidationError):
        RequestFrame.capture(original.request, original.footprint(),
                             prepared_by='runtime-fixture', planning_actor='fixture')
    wrong = CheckpointRequest.model_validate({**original.request.model_dump(), 'planning_request_sha256': 'f' * 64})
    with pytest.raises(ValueError, match='planning_request_digest_mismatch'):
        CheckpointRequestBinding.bind(wrong, original.footprint(), actor_id='fixture')


@pytest.mark.parametrize('raw', [b'[]', b'{"profile":"unknown"}', b''])
def test_frame_dispatch_rejects_unknown_or_empty_profile(raw):
    with pytest.raises(ValueError, match='frame_profile|frame_size'):
        read_frame(raw)
