import json
from types import SimpleNamespace

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.workers.configuration import ConfigurationPins, load_workers


def test_planning_templates_and_runtime_graph_materials_are_pinned(tmp_path):
    for name in ('template', 'graph', 'descriptor', 'schema', 'policy', 'recipe'):
        (tmp_path / name).write_bytes(b'original')
    planning = tmp_path / 'planning.json'
    planning.write_text(json.dumps({'templates': [{'path': 'template'}]}))
    runtime = tmp_path / 'runtime.json'
    runtime.write_text(json.dumps({'graphs': [{'definition': 'graph',
        'releases': [{'descriptor': 'descriptor'}], 'schemas': [{'path': 'schema'}]}],
        'supervision_admission': {'policies': ['policy'], 'recipes': ['recipe']}}))
    p = ConfigurationPins.bind('planning-checkpoint', planning)
    r = ConfigurationPins.bind('runtime-coordinate', runtime)
    assert len(p.files) == 2 and len(r.files) == 6
    for pins in (p, r):
        pins.verify()
        for path, _ in pins.files:
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            with pytest.raises(ProfileError, match='configuration_changed'):
                pins.verify()
            path.write_bytes(original)


@pytest.mark.parametrize('reference', ['../escape', '/absolute', 'Z:/external', 'Z:relative', ''])
@pytest.mark.parametrize('name', ['planning-checkpoint', 'planning-curation'])
def test_config_reference_escape_is_rejected(tmp_path, reference, name):
    path = tmp_path / 'worker.json'
    path.write_text(json.dumps({'templates': [{'path': reference}]} if name == 'planning-checkpoint' else {'policies': [reference]}))
    with pytest.raises(ProfileError, match='reference_path'):
        ConfigurationPins.bind(name, path)


def test_worker_sidecar_has_no_arbitrary_command_or_missing_owner(tmp_path):
    path = tmp_path / 'workers.json'
    record = {'profile': 'local-native-workers-v1', 'workers': {'arbitrary': {}}}
    path.write_text(json.dumps(record))
    with pytest.raises(ProfileError, match='manifest_names'):
        load_workers(path, {})
    record['workers'] = {'runtime-coordinate': {'configuration': 'unused', 'source_lock': 'unused', 'scope': None}}
    path.write_text(json.dumps(record))
    with pytest.raises(ProfileError, match='serving_owner_required'):
        load_workers(path, {})


def test_live_worker_key_is_explicit_and_missing_key_fails_before_pin(tmp_path, monkeypatch):
    config = tmp_path / 'planning.json'
    config.write_text(json.dumps({'provider': 'openai_checkpoint_v1', 'live': {
        'key_env': 'AMPHORA_OPENAI_API_KEY', 'egress': 'approved_synthetic_engineering_only'}}))
    sidecar = tmp_path / 'workers.json'
    sidecar.write_text(json.dumps({'profile': 'local-native-workers-v1', 'workers': {'planning-checkpoint': {
        'configuration': str(config), 'source_lock': 'unused', 'scope': None}}}))
    monkeypatch.delenv('AMPHORA_OPENAI_API_KEY', raising=False)
    with pytest.raises(ProfileError, match='live_key_missing'):
        load_workers(sidecar, {'planning': SimpleNamespace(environment={})})


def test_worker_sidecar_pins_same_serving_installation_and_live_environment(tmp_path, monkeypatch):
    from amphora_deployment.workers.native import NativeBinding
    config = tmp_path / 'planning.json'
    config.write_text(json.dumps({'provider': 'openai_checkpoint_v1', 'live': {
        'key_env': 'AMPHORA_OPENAI_API_KEY', 'egress': 'approved_synthetic_engineering_only'}}))
    manifest = tmp_path / 'workers.json'
    manifest.write_text(json.dumps({'profile': 'local-native-workers-v1', 'workers': {'planning-checkpoint': {
        'configuration': str(config), 'source_lock': str(tmp_path / 'lock'), 'scope': None}}}))
    installation = object()
    captured = []
    def pin(*args):
        captured.append(args)
        return SimpleNamespace(installation=installation)
    monkeypatch.setattr(NativeBinding, 'pin', pin)
    monkeypatch.setenv('AMPHORA_OPENAI_API_KEY', 'synthetic-key')
    owner = SimpleNamespace(environment={}, directory=tmp_path, installation=installation)
    assert set(load_workers(manifest, {'planning': owner})) == {'planning-checkpoint'}
    assert captured[0][4] == {'AMPHORA_OPENAI_API_KEY': 'synthetic-key'}
    assert owner.environment == {}
    owner.installation = object()
    with pytest.raises(ProfileError, match='serving_installation_mismatch'):
        load_workers(manifest, {'planning': owner})


@pytest.mark.parametrize('policies', [None, [], ['same', 'same'], [1], ['p' + str(i) for i in range(33)]])
def test_curation_policy_pins_reject_missing_duplicate_and_unbounded_files(tmp_path, policies):
    path = tmp_path / 'curation.json'
    path.write_text(json.dumps({'policies': policies}))
    with pytest.raises(ProfileError, match='curation_policy_references'):
        ConfigurationPins.bind('planning-curation', path)


def test_curation_policy_content_is_pinned_before_process_launch(tmp_path):
    policy = tmp_path / 'policy.json'; policy.write_text('{}')
    configuration = tmp_path / 'curation.json'; configuration.write_text(json.dumps({'policies': ['policy.json']}))
    pins = ConfigurationPins.bind('planning-curation', configuration)
    assert len(pins.files) == 2
    pins.verify()
    policy.write_text('{"changed":true}')
    with pytest.raises(ProfileError, match='configuration_changed'):
        pins.verify()


@pytest.mark.parametrize('provider', ['disabled', 'openai_curation_v1', 'openai_checkpoint_v1'])
def test_curation_recipe_preserves_owner_environment_and_requires_explicit_live_settings(tmp_path, monkeypatch, provider):
    from amphora_deployment.workers.native import NativeBinding
    configuration = tmp_path / 'curation.json'
    record = {'provider': provider, 'policies': ['policy.json']}
    if provider == 'openai_curation_v1':
        record['live'] = {'key_env': 'AMPHORA_OPENAI_API_KEY', 'egress': 'approved_synthetic_engineering_only'}
    configuration.write_text(json.dumps(record))
    manifest = tmp_path / 'workers.json'; manifest.write_text(json.dumps({'profile': 'local-native-workers-v1', 'workers': {'planning-curation': {'configuration': str(configuration), 'source_lock': str(tmp_path/'lock'), 'scope': None}}}))
    identity = object(); captured = []
    def pin(*args):
        captured.append(args)
        return SimpleNamespace(installation=identity)
    monkeypatch.setattr(NativeBinding, 'pin', pin)
    monkeypatch.setenv('AMPHORA_OPENAI_API_KEY', 'synthetic-key')
    owner = SimpleNamespace(environment={'AMPHORA_PLANNING_DATABASE_URL':'scoped-test'}, directory=tmp_path, installation=identity)
    if provider == 'openai_checkpoint_v1':
        with pytest.raises(ProfileError, match='curation_provider'): load_workers(manifest, {'planning': owner})
        assert captured == []
        return
    assert set(load_workers(manifest, {'planning': owner})) == {'planning-curation'}
    expected = dict(owner.environment)
    if provider == 'openai_curation_v1': expected['AMPHORA_OPENAI_API_KEY'] = 'synthetic-key'
    assert captured[0][4] == expected and owner.environment == {'AMPHORA_PLANNING_DATABASE_URL':'scoped-test'}
    if provider == 'openai_curation_v1':
        monkeypatch.delenv('AMPHORA_OPENAI_API_KEY')
        with pytest.raises(ProfileError, match='live_key_missing'): load_workers(manifest, {'planning': owner})
        record['live']['egress'] = 'unreviewed'
        configuration.write_text(json.dumps(record))
        with pytest.raises(ProfileError, match='live_policy'): load_workers(manifest, {'planning': owner})
