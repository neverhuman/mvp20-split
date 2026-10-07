import json

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.scientific_workers.journal import ContainerJournal


@pytest.fixture
def journal(tmp_path):
    return ContainerJournal(tmp_path / 'turn.json', 'a' * 32, 'evolution-seed', 'b' * 64)


def test_only_released_original_turn_allows_a_new_identity(journal):
    assert journal.read() is None
    first = journal.intent()
    for operation in (journal.intent, journal.starting, journal.released):
        with pytest.raises(ProfileError):
            operation()
    journal.created('c' * 64)
    journal.starting()
    journal.started()
    journal.started()
    journal.exited(0)
    journal.exited(0)
    with pytest.raises(ProfileError, match='exit_changed'):
        journal.exited(1)
    journal.released()
    journal.released()
    second = journal.intent()
    assert second['turn_id'] != first['turn_id'] and second['sequence'] == 2


def test_starting_survives_relaunch_and_never_allows_another_start(journal):
    journal.intent()
    journal.created('c' * 64)
    journal.starting()
    replacement = ContainerJournal(journal.path, journal.deployment_id, journal.worker, journal.binding_sha256)
    assert replacement.read()['phase'] == 'starting'
    for operation in (replacement.starting, replacement.intent):
        with pytest.raises(ProfileError):
            operation()
    # A start response can be lost even though the container completed.
    replacement.exited(3)
    assert replacement.read()['exit_code'] == 3


def test_failed_atomic_replace_preserves_original_intent(journal, monkeypatch):
    original = journal.intent()
    def fail(*_):
        raise OSError('disk unavailable')
    monkeypatch.setattr('amphora_deployment.scientific_workers.journal.os.replace', fail)
    with pytest.raises(OSError):
        journal.created('c' * 64)
    assert journal.read() == original
    assert list(journal.path.parent.glob('.turn-*.tmp')) == []


@pytest.mark.parametrize('field,value', [('deployment_id', 'd' * 32), ('binding_sha256', 'e' * 64),
    ('phase', 'invented'), ('container_id', 'truncated'), ('sequence', True), ('exit_code', 0),
    ('updated_at', 'yesterday')])
def test_malformed_or_rebound_journal_rejected(journal, field, value):
    record = journal.intent()
    record[field] = value
    journal.path.write_text(json.dumps(record))
    with pytest.raises(ProfileError):
        journal.read()
