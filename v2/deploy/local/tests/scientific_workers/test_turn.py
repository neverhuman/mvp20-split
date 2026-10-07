from types import SimpleNamespace

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.scientific_workers.engine import ContainerObservation
from amphora_deployment.scientific_workers.journal import ContainerJournal
from amphora_deployment.scientific_workers.turn import ContainerTurn


class Engine:
    def __init__(self):
        self.observed = None
        self.creates, self.starts, self.removes = 0, 0, 0
        self.lose_create = self.lose_start = self.lose_remove = False

    def observe(self, *_):
        return self.observed

    def create(self, *_):
        self.creates += 1
        self.observed = ContainerObservation('c' * 64, 'created', False, 0)
        if self.lose_create:
            raise ProfileError('container_engine_unavailable')
        return self.observed.container_id

    def start(self, *_):
        self.starts += 1
        self.observed = ContainerObservation('c' * 64, 'running', True, 0)
        if self.lose_start:
            raise ProfileError('container_engine_unavailable')

    def remove_exited(self, *_):
        assert self.observed is None or self.observed.status == 'exited'
        self.removes += 1
        self.observed = None
        if self.lose_remove:
            raise ProfileError('container_engine_unavailable')


def create(tmp_path):
    journal = ContainerJournal(tmp_path / 'turn.json', 'a' * 32, 'evolution-seed', 'b' * 64)
    engine = Engine()
    return ContainerTurn(journal, engine, SimpleNamespace(verify=lambda: None), {}), journal, engine


def test_lost_create_reuses_original_container_and_turn_identity(tmp_path):
    turn, journal, engine = create(tmp_path)
    engine.lose_create = True
    with pytest.raises(ProfileError):
        turn.launch()
    original = journal.read()['turn_id']
    engine.lose_create = False
    turn.launch()
    assert engine.creates == engine.starts == 1
    assert journal.read()['turn_id'] == original
    assert turn.poll() is None


@pytest.mark.parametrize('state', ['created', 'running', 'exited'])
def test_lost_start_recovery_never_restarts_original_container(tmp_path, state):
    turn, journal, engine = create(tmp_path)
    engine.lose_start = True
    with pytest.raises(ProfileError):
        turn.launch()
    assert journal.read()['phase'] == 'starting'
    engine.observed = ContainerObservation('c' * 64, state, state != 'created', 0)
    replacement = ContainerTurn(journal, engine, turn.profile, {})
    replacement.launch()
    assert replacement.poll() == (0 if state == 'exited' else None)
    assert engine.creates == engine.starts == 1
    if state != 'exited':
        with pytest.raises(ProfileError, match='release_requires_exit'):
            replacement.release()


def test_lost_removal_reconciles_without_reexecution(tmp_path):
    turn, journal, engine = create(tmp_path)
    turn.launch()
    engine.observed = ContainerObservation('c' * 64, 'exited', True, 3)
    assert turn.poll() == 3
    engine.lose_remove = True
    with pytest.raises(ProfileError):
        turn.release()
    assert journal.read()['phase'] == 'exited'
    engine.lose_remove = False
    turn.release()
    turn.release()
    assert journal.read()['phase'] == 'released'
    assert engine.creates == engine.starts == 1


def test_disappeared_original_does_not_become_a_fresh_turn(tmp_path):
    turn, journal, engine = create(tmp_path)
    turn.launch()
    engine.observed = None
    with pytest.raises(ProfileError, match='original_missing'):
        turn.poll()
    turn.launch()
    assert engine.creates == engine.starts == 1
    assert journal.read()['phase'] == 'started'
