import json
import pytest

from amphora_deployment.campaign_launch.intent import LaunchError
from amphora_deployment.campaign_launch.run_bindings import RunBindingStore
from amphora_deployment.campaign_launch.state import LaunchState
from amphora_deployment.scientific_workers.configuration import ScientificBinding
from amphora_deployment.scientific_workers.profiles import ToolProfile


@pytest.fixture
def bindings_setup(tmp_path, make_intent, admission_receipt, clock):
    root = tmp_path / 'installation'
    root.mkdir()
    certificate = root / 'trust.pem'; certificate.write_bytes(b'trust-fixture')
    config = root / 'template.json'
    config.write_text(json.dumps({'actor_id': 'scientific-worker',
        'scope': {'tenant_id': 'internal', 'project_id': 'demo'}, 'run_id': 'prior-run',
        'image_sha256': 'a' * 64,
        'runtime': {'endpoint': 'https://host.docker.internal:57118', 'token_env': 'AMPHORA_RUNTIME_TOKEN'},
        'artifacts': {'endpoint': 'https://host.docker.internal:57112', 'token_env': 'AMPHORA_ARTIFACT_TOKEN'}}))
    profile = ToolProfile.pin('hansen-solvency', 'sha256:' + 'a' * 64, config, certificate, 57118, 57112)
    template = ScientificBinding.pin(root, 'b' * 32, profile,
        {'AMPHORA_RUNTIME_TOKEN': 'runtime-private', 'AMPHORA_ARTIFACT_TOKEN': 'artifact-private'})
    store = RunBindingStore(root, 'b' * 32, {'hansen-solvency': template}, runtime_port=57118, artifact_port=57112)
    intent = make_intent()
    state = LaunchState.initial(intent, clock()).move('admission_unresolved', clock())
    return store, state.observe_admission(admission_receipt(intent), clock()), template


def test_binding_restart_is_identical_and_preserves_template(bindings_setup):
    store, state, template = bindings_setup
    original = template.profile.configuration.read_bytes()
    first = store.prepare(state)['hansen-solvency']
    reopened = RunBindingStore(store.root, store.deployment_id, store.templates,
        runtime_port=store.runtime_port, artifact_port=store.artifact_port)
    second = reopened.prepare(state)['hansen-solvency']
    assert first.profile == second.profile and first.journal.path == second.journal.path
    assert json.loads(first.profile.configuration.read_bytes())['run_id'] == 'run-1'
    assert template.profile.configuration.read_bytes() == original
    assert first.profile.fingerprint != template.profile.fingerprint
    raw = (store.directory(state) / 'bindings.json').read_bytes()
    assert b'private' not in raw and b'run-1' in raw
    assert first.journal.read() is None  # Retaining a binding cannot start a turn.


def test_changed_retained_binding_cannot_be_overwritten(bindings_setup):
    store, state, _ = bindings_setup
    store.prepare(state)
    path = store.directory(state) / 'hansen-solvency.json'
    value = json.loads(path.read_bytes()); value['run_id'] = 'wrong-run'
    path.write_text(json.dumps(value))
    with pytest.raises(LaunchError, match='launch_worker_binding_changed'):
        store.prepare(state)
    assert json.loads(path.read_bytes())['run_id'] == 'wrong-run'


def test_incomplete_file_set_can_resume_without_new_identity(bindings_setup):
    store, state, _ = bindings_setup
    original = store.prepare(state)['hansen-solvency']
    (store.directory(state) / 'bindings.json').unlink()
    resumed = store.prepare(state)['hansen-solvency']
    assert resumed.profile.fingerprint == original.profile.fingerprint


def test_configuration_before_admission_is_forbidden(bindings_setup, clock):
    store, state, _ = bindings_setup
    with pytest.raises(LaunchError, match='launch_admission_required'):
        store.prepare(LaunchState.initial(state.intent, clock()))
