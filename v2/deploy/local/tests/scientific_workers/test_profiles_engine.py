import json
from types import SimpleNamespace

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.scientific_workers.engine import (
    ContainerEngine,
    ContainerObservation,
    name_for,
)
from amphora_deployment.scientific_workers.journal import ContainerJournal


def test_profile_pins_exact_files_and_closed_entrypoint(profile):
    assert profile.entrypoint == ('python', '-m', 'amphora_evolution_search')
    assert profile.arguments == ('worker', '--operation', 'seed', '--config', '/amphora/worker.json')
    original = profile.fingerprint
    profile.verify()
    profile.configuration.write_bytes(profile.configuration.read_bytes() + b' ')
    assert profile.fingerprint == original
    with pytest.raises(ProfileError, match='configuration_changed'):
        profile.verify()


def test_observation_rejects_identity_labels_image_and_state_drift(tmp_path, profile):
    journal = ContainerJournal(tmp_path / 'turn.json', 'b' * 32, profile.name, profile.fingerprint)
    expected = journal.intent()
    record = {'id': 'c' * 64, 'name': '/' + name_for(expected), 'image': profile.image_id,
        'deployment': expected['deployment_id'], 'binding': profile.fingerprint, 'turn': expected['turn_id'],
        'worker': profile.name, 'status': 'created', 'started_at': '0001-01-01T00:00:00Z', 'exit_code': 0}
    assert ContainerObservation.bind(record, expected, profile.image_id).started is False
    for field in ('name', 'image', 'deployment', 'binding', 'turn', 'worker', 'id', 'status'):
        with pytest.raises(ProfileError):
            ContainerObservation.bind(record | {field: 'foreign'}, expected, profile.image_id)
    with pytest.raises(ProfileError, match='start_observation'):
        ContainerObservation.bind(record | {'status': 'running'}, expected, profile.image_id)


def test_create_never_places_credentials_in_arguments_or_mounts_private_key(profile, tmp_path, monkeypatch):
    journal = ContainerJournal(tmp_path / 'turn.json', 'b' * 32, profile.name, profile.fingerprint)
    record = journal.intent()
    engine, calls = ContainerEngine(), []
    monkeypatch.setattr(engine, 'verify_image', lambda _: None)
    def run(*args, environment=None):
        calls.append((args, environment))
        return 'c' * 64
    monkeypatch.setattr(engine, '_run', run)
    assert engine.create(record, profile, {'AMPHORA_RUNTIME_TOKEN': 'private-runtime',
                                         'AMPHORA_ARTIFACT_TOKEN': 'private-artifact'}) == 'c' * 64
    arguments = ' '.join(calls[0][0])
    assert 'private-' not in arguments and 'encrypted-key' not in arguments
    assert '--read-only' in arguments and '--restart no' in arguments and '--log-driver none' in arguments
    assert profile.image_id in arguments and '--rm' not in arguments


def test_engine_failure_is_not_missing_container(monkeypatch):
    monkeypatch.setattr('amphora_deployment.scientific_workers.engine.subprocess.run',
                        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout='', stderr='private'))
    with pytest.raises(ProfileError, match='container_engine_operation_failed') as error:
        ContainerEngine()._run('container', 'ls')
    assert 'private' not in str(error.value)


@pytest.mark.parametrize(('field', 'bad'), [('os', 'windows'), ('arch', 'aarch64'), ('cpus', True),
    ('cpus', 0), ('memory', False), ('memory', 0)])
def test_engine_resource_observations_reject_wrong_platform_or_unknown_capacity(monkeypatch, field, bad):
    engine = ContainerEngine()
    value = {'os': 'linux', 'arch': 'x86_64', 'cpus': 10, 'memory': 5 * 1024**3}
    monkeypatch.setattr(engine, '_run', lambda *_: json.dumps(value))
    assert engine.resources() == value
    value[field] = bad
    with pytest.raises(ProfileError, match='engine_resources'):
        engine.resources()
