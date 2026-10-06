"""Versioned intake preserves original receipts without provider work."""

import hashlib
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.supervision_intake import SupervisionIntake
from amphora_agent_planning.supervision_intake.commands import IncomingRequest
from amphora_agent_planning.supervision_intake.snapshot import (
    CheckpointIntakeSnapshot,
    IntakeSnapshot,
    read_snapshot,
)
from amphora_contracts_planning import checkpoint_draft_schema
from amphora_contracts_supervision import CheckpointRequest, parse_checkpoint_command
from pydantic import ValidationError
from sqlalchemy import text

from .support import FIXTURES, principal
from .support import command as old_command
from .support import request as old_request


def test_new_output_profile_requires_explicit_checkpoint_request():
    actor = principal()
    value = request(actor)
    data = value.model_dump(mode='json')
    data['planning_request']['context']['output_schema'] = checkpoint_draft_schema().model_dump(mode='json')
    changed = CheckpointRequest.model_validate_json(json.dumps(data))
    from amphora_agent_planning.supervision_intake.snapshot import encoded
    data['planning_request_sha256'] = hashlib.sha256(encoded(changed.planning_request)).hexdigest()
    accepted = CheckpointIntakeSnapshot.bind(CheckpointRequest.model_validate_json(json.dumps(data)), actor)
    assert accepted.planning.document().context.output_schema == checkpoint_draft_schema()
    legacy = old_request(actor).model_dump(mode='json')
    legacy.update(planning_request=data['planning_request'], planning_request_sha256=data['planning_request_sha256'])
    with pytest.raises(ValueError, match='checkpoint_output_requires_checkpoint_request'):
        IntakeSnapshot.from_bytes(json.dumps(legacy).encode(), actor)


def request(actor):
    old = old_request(actor)
    data = json.loads((FIXTURES / 'checkpoint-request.json').read_bytes())
    data.update(reference=old.reference.model_dump(mode='json'), policy=old.policy.model_dump(mode='json'),
        planning_request=old.planning_request.model_dump(mode='json'), planning_request_sha256=old.planning_request_sha256)
    data['snapshot']['cut'] = old.snapshot.cut.model_dump(mode='json')
    return CheckpointRequest.model_validate_json(json.dumps(data))


def command(value, key='checkpoint-command'):
    return parse_checkpoint_command(json.dumps({'encoding': 'amphora-command-v2', 'identity': {
        'scope': value.reference.scope.model_dump(mode='json'), 'actor_id': value.planning_request.actor_id,
        'command_family': 'planning.supervision.request.v2', 'command_id': key}, 'payload': value.model_dump(mode='json')}))


def test_pure_v2_intake_and_closed_v1_parser():
    actor = principal()
    value = request(actor)
    incoming = IncomingRequest.bind(actor, command(value))
    assert type(incoming.snapshot) is CheckpointIntakeSnapshot
    assert read_snapshot(incoming.snapshot.canonical, actor) == incoming.snapshot
    with pytest.raises(ValidationError):
        IntakeSnapshot.from_bytes(incoming.snapshot.canonical, actor)
    for raw in (b'[]', b'{"schema_version":"3"}'):
        with pytest.raises(ValueError, match='supervision_request_profile'):
            read_snapshot(raw, actor)


@pytest.mark.parametrize('change,reason', [
    ('duplicate', 'supervision_duplicate_field'), ('kind', 'supervision_target_kind_mismatch'),
])
def test_target_shape_checks_do_not_grant_runtime_authority(change, reason):
    actor = principal()
    data = request(actor).model_dump(mode='json')
    if change == 'duplicate':
        data['snapshot']['checkpoints'][0]['fields'] *= 2
    else:
        data['snapshot']['reads'][0]['node']['kind'] = 'invoke'
    with pytest.raises(ValueError, match=reason):
        IncomingRequest.bind(actor, command(CheckpointRequest.model_validate_json(json.dumps(data))))


def test_actual_intake_replacement_and_family_specific_receipt(stored):
    e = stored
    intake = SupervisionIntake(e.engine)
    value = request(e.principal)
    incoming = command(value)
    first = intake.receive(e.principal, incoming)
    assert first.outcome.status == 'recorded'
    replacement = SupervisionIntake(e.engine)
    reader = replace(e.principal, actions=frozenset({'read_attempts'}))
    assert replacement.receive(e.principal, incoming) == first
    assert replacement.receipt(reader, incoming.identity.command_id, family=incoming.identity.command_family) == first
    assert replacement.receipt(reader, incoming.identity.command_id) is None
    assert replacement.request(reader, value.planning_request.reference.engagement_id).document() == value
    conflict = replacement.receive(e.principal, old_command(old_request(e.principal), incoming.identity.command_id))
    assert conflict.outcome.status == 'rejected' and conflict.outcome.reason_code == 'supervision_request_conflict'
    assert replacement.receipt(reader, incoming.identity.command_id, family=incoming.identity.command_family) == first
    with e.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.attempts WHERE tenant_id=:tenant AND project_id=:project'),
            {'tenant': reader.scope.tenant_id, 'project': reader.scope.project_id}).scalar_one() == 0


def test_wrapper_and_receipt_rollback_together(stored, monkeypatch):
    e = stored
    intake = SupervisionIntake(e.engine)
    value = request(e.principal)
    def fail(*args):
        raise RuntimeError('before-receipt')
    monkeypatch.setattr(intake, '_record_command', fail)
    with pytest.raises(RuntimeError, match='before-receipt'):
        intake.receive(e.principal, command(value))
    assert intake.request(e.principal, value.planning_request.reference.engagement_id) is None
