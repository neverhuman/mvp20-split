import copy
import json

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.tool_catalog.heartbeat import HeartbeatJournal, ReplicaBinding


def journal(tmp_path):
    return HeartbeatJournal(tmp_path / 'heartbeat.json',
        ReplicaBinding('installation', 'internal', 'synthetic', 'worker', 'seed-release', 'seed-slot'))


def receipt(command):
    payload = command['payload']
    return {'schema_version': '1', 'operation_id': 'registry-operation', 'status': 'accepted',
        'reason_code': 'observed', 'release': None, 'deployment': None, 'decision': None,
        'heartbeat': {'scope': command['identity']['scope'], 'deployment_id': payload['deployment_id'],
            'replica_id': payload['replica_id'], 'worker_id': command['identity']['actor_id'],
            'revision': payload['expected_revision'] + 1, 'free_slots': payload['free_slots'],
            'observed_at': '2026-01-01T00:00:00Z', 'expires_at': '2026-01-01T00:00:15Z'}}


def test_lost_response_survives_restart_but_cannot_replay_positive_when_unready(tmp_path):
    first = journal(tmp_path)
    command = first.prepare(ready=True)
    raw = first.path.read_bytes()
    replacement = journal(tmp_path)
    assert replacement.prepare(ready=False) is None
    assert replacement.path.read_bytes() == raw
    assert replacement.prepare(ready=True) == command
    observed = replacement.accept(receipt(command))
    assert observed['expires_at'] == '2026-01-01T00:00:15Z'  # Historical replay is not renewed.
    withdrawal = replacement.prepare(ready=False)
    assert withdrawal['identity']['command_id'] != command['identity']['command_id']
    assert withdrawal['payload']['expected_revision'] == 1
    assert withdrawal['payload']['free_slots'] == 0
    assert replacement.prepare(ready=True) == withdrawal  # Resolve pending zero before new positive.
    replacement.accept(receipt(withdrawal))
    renewed = replacement.prepare(ready=True)
    assert renewed['payload']['expected_revision'] == 2
    assert renewed['payload']['replica_id'] == command['payload']['replica_id']


@pytest.mark.parametrize(('field', 'value'), [
    ('scope', {'tenant_id': 'foreign', 'project_id': 'synthetic'}),
    ('deployment_id', 'other'), ('replica_id', 'other'), ('worker_id', 'other'),
    ('revision', 2), ('revision', True), ('free_slots', 0), ('free_slots', True),
    ('observed_at', '2026-01-01T00:00:00'), ('expires_at', '2026-01-01T00:00:16Z'),
    ('expires_at', None),
])
def test_foreign_or_malformed_receipt_retains_original_intent(tmp_path, field, value):
    owner = journal(tmp_path)
    command = owner.prepare(ready=True)
    raw = owner.path.read_bytes()
    response = receipt(command)
    response['heartbeat'][field] = value
    with pytest.raises(ProfileError):
        owner.accept(response)
    assert owner.path.read_bytes() == raw


def test_rejection_cannot_reset_revision_or_replace_original_command(tmp_path):
    owner = journal(tmp_path)
    command = owner.prepare(ready=False)
    response = receipt(command)
    response.update(status='rejected', reason_code='revision_conflict', heartbeat=None)
    with pytest.raises(ProfileError, match='not_accepted'):
        owner.accept(response)
    assert owner.prepare(ready=False) == command


def test_journal_binding_corruption_and_oversize_fail_closed(tmp_path):
    owner = journal(tmp_path)
    owner.prepare(ready=True)
    original = json.loads(owner.path.read_bytes())
    for mutate in ('binding', 'revision', 'pending'):
        bad = copy.deepcopy(original)
        if mutate == 'binding':
            bad['binding']['project_id'] = 'other'
        elif mutate == 'revision':
            bad['revision'] = True
        else:
            bad['pending']['payload']['expected_revision'] = False
        owner.path.write_text(json.dumps(bad), encoding='utf-8')
        with pytest.raises(ProfileError):
            owner.prepare(ready=True)
    owner.path.write_bytes(b' ' * 8193)
    with pytest.raises(ProfileError, match='journal_size'):
        owner.read()


def test_journal_write_failure_prevents_delivery_and_preserves_previous_state(tmp_path, monkeypatch):
    owner = journal(tmp_path)
    first = owner.prepare(ready=True)
    original = owner.path.read_bytes()
    def fail_replace(*_):
        raise OSError('simulated interruption before replace')
    monkeypatch.setattr('amphora_deployment.tool_catalog.heartbeat.os.replace', fail_replace)
    with pytest.raises(OSError):
        owner.accept(receipt(first))
    assert owner.path.read_bytes() == original
    assert list(tmp_path.glob('*.tmp')) == []
    assert owner.prepare(ready=True) == first
