"""Explicit request family, closed predecessor parsers and exact wire fixtures."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_supervision import (
    CheckpointRequest,
    SupervisionRequest,
    parse_checkpoint_command,
    parse_supervision_command,
)
from pydantic import ValidationError

FIXTURES = Path(__file__).parent / 'fixtures'


def test_exact_checkpoint_request_and_command_roundtrip():
    raw = (FIXTURES / 'checkpoint-command.json').read_bytes()
    command = parse_checkpoint_command(raw)
    assert command.canonical_bytes == raw
    request = CheckpointRequest.model_validate_json((FIXTURES / 'checkpoint-request.json').read_bytes())
    assert request.snapshot.checkpoints[0].fields == ('temperature',)
    assert CheckpointRequest.model_validate_json(request.model_dump_json()) == request
    pins = json.loads((FIXTURES / 'checkpoint-pins.json').read_bytes())
    for name, digest in pins.items():
        assert hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest() == digest


def test_old_parsers_never_reinterpret_new_targets():
    with pytest.raises(ValidationError):
        SupervisionRequest.model_validate_json((FIXTURES / 'checkpoint-request.json').read_bytes())
    with pytest.raises(ValidationError):
        CheckpointRequest.model_validate_json((FIXTURES / 'request.json').read_bytes())
    with pytest.raises(CommandEncodingError):
        parse_supervision_command('planning.supervision.request.v2', (FIXTURES / 'checkpoint-command.json').read_bytes())
    with pytest.raises(CommandEncodingError):
        parse_checkpoint_command((FIXTURES / 'request-command.json').read_bytes())


@pytest.mark.parametrize('changes', [
    {'fields': []}, {'fields': ['x'] * 65}, {'fields': ['']},
    {'kind': 'invoke', 'fields': ['temperature']}, {'kind': 'artifact_project'},
    {'activation_id': 'wrong'}, {'accepted': True},
])
def test_malformed_target_shapes_reject(changes):
    doc = json.loads((FIXTURES / 'checkpoint-request.json').read_bytes())
    doc['snapshot']['checkpoints'][0].update(changes)
    with pytest.raises(ValidationError):
        CheckpointRequest.model_validate_json(json.dumps(doc))


@pytest.mark.parametrize('part,key,value', [
    ('identity', 'actor_id', 'other'),
    ('identity', 'scope', {'tenant_id': 'other', 'project_id': 'context'}),
])
def test_actor_and_scope_binding_reject(part, key, value):
    doc = json.loads((FIXTURES / 'checkpoint-command.json').read_bytes())
    doc[part][key] = value
    with pytest.raises(CommandEncodingError):
        parse_checkpoint_command(json.dumps(doc))


def test_invoke_review_shape_has_no_scalar_fields():
    doc = json.loads((FIXTURES / 'checkpoint-request.json').read_bytes())
    doc['snapshot']['checkpoints'][0].update(kind='invoke', fields=[])
    assert CheckpointRequest.model_validate_json(json.dumps(doc)).snapshot.checkpoints[0].fields == ()
