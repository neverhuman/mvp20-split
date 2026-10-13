import json
import subprocess
import sys
from uuid import uuid4

import pytest

from amphora_agent_planning.curation_worker.configuration import ReviewedConfiguration, WorkerConfiguration
from amphora_agent_planning.curation_worker.hosting import CurationHost
from amphora_agent_planning.curation_worker.peers import CurationPeers
from ..curation_policy.test_policy import config as policy_config


def files(tmp_path, monkeypatch, *, live=False):
    policy = policy_config()
    scope = {'tenant_id': 'curation-configuration', 'project_id': uuid4().hex}
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}:
                value.update(scope)
            for item in value.values(): rescope(item)
        elif isinstance(value, list):
            for item in value: rescope(item)
    rescope(policy)
    template = policy['template']
    config = {'database_url_env': 'CURATION_TEST_DATABASE', 'actor_id': template['actor_id'],
        'scope': template['reference']['scope'], 'worker_id': 'managed-test', 'policies': ['policy.json'],
        'runtime_owner': 'runtime', 'eligibility': {'owner_id': 'registry-fixture',
            'actor_id': template['actor_id'], 'policy_sha256': 'c' * 64, 'maximum_age_seconds': 5}}
    for index, name in enumerate(('data', 'runtime', 'registry', 'knowledge', 'research')):
        key = 'CURATION_TEST_' + name.upper()
        monkeypatch.setenv(key, 'x' * 40)
        config[name] = {'endpoint': 'http://127.0.0.1:' + str(59000 + index), 'token_env': key}
    if live:
        config['provider'] = 'openai_curation_v1'
        config['live'] = {'key_env': 'CURATION_TEST_MODEL_KEY', 'scope': config['scope'],
            'egress': 'approved_synthetic_engineering_only'}
        monkeypatch.delenv('CURATION_TEST_MODEL_KEY', raising=False)
    path = tmp_path / 'worker.json'
    path.write_text(json.dumps(config), encoding='utf-8')
    (tmp_path / 'policy.json').write_text(json.dumps(policy), encoding='utf-8')
    return path, config, policy


def test_public_client_composition_does_not_read_model_key_or_call_peers(tmp_path, monkeypatch):
    path, config, policy = files(tmp_path, monkeypatch, live=True)
    reviewed = ReviewedConfiguration.load(path)
    peers = CurationPeers.bind(reviewed)
    assert peers.runtime.owner_id == 'runtime' and peers.registry.owner_id == 'registry-fixture'
    assert peers.artifacts.identity.actor_id == config['actor_id']
    assert peers.assembler.artifacts.reader.data is peers.data
    assert peers.refresh.artifacts.data is peers.data
    assert list(reviewed.policy_map()) == ['synthetic']
    assert peers.runtime.actor_id == peers.registry.actor_id == config['actor_id']


def test_v2_preserves_requester_and_binds_explicit_peer_actors(tmp_path, monkeypatch, planning_database):
    path, config, policy = files(tmp_path, monkeypatch)
    config.update(profile='planning-curation-worker.v2', runtime_actor_id='planning-author')
    config['eligibility']['actor_id'] = 'planning-reader'
    path.write_text(json.dumps(config))
    reviewed = ReviewedConfiguration.load(path)
    peers = CurationPeers.bind(reviewed)
    assert peers.runtime.actor_id == 'planning-author'
    assert peers.registry.actor_id == 'planning-reader'
    assert peers.artifacts.identity.actor_id == config['actor_id']
    assert reviewed.policies[0].document().template.actor_id == config['actor_id']
    monkeypatch.setenv('CURATION_TEST_DATABASE', planning_database.render_as_string(hide_password=False))
    host = CurationHost.load(path)
    try:
        assert host.principal.actor_id == config['actor_id']
        assert host.poller.worker.compiler.journal.store.runtime_actor == 'planning-author'
        assert host.poller.worker.compiler.journal.store.eligibility == reviewed.eligibility()
    finally:
        host.close()


@pytest.mark.parametrize('profile,actor', [('planning-curation-worker.v1','planning-author'),
    ('planning-curation-worker.v2',None)])
def test_peer_actor_selection_requires_explicit_v2_profile(tmp_path,monkeypatch,profile,actor):
    path,config,_ = files(tmp_path,monkeypatch)
    config.update(profile=profile,runtime_actor_id=actor)
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError):ReviewedConfiguration.load(path)


def test_composed_refresh_and_acceptance_use_real_reader_interfaces(tmp_path, monkeypatch):
    from amphora_agent_planning.metadata_reads import MetadataWindow
    from ..campaign_context.test_selection import request
    from ..registry_access.test_discovery import Scripted, record
    from ..runtime_metadata.test_reader import universe

    path, _, _ = files(tmp_path, monkeypatch)
    peers = CurationPeers.bind(ReviewedConfiguration.load(path))
    release, reviewed = record(), universe()
    registry_wire = Scripted(release, release)
    runtime_wire = Scripted(reviewed)
    monkeypatch.setattr(peers.assembler.registry.transport, 'read', registry_wire.read)
    monkeypatch.setattr(peers.assembler.runtime.transport, 'read', runtime_wire.read)
    # Refresh needs validated readers; capability acceptance needs the public
    # metadata transport. Exercise both interfaces after production composition.
    selected = peers.refresh.registry.exact(request(), release.lock, MetadataWindow('registry'))
    assert selected.document() == release
    assert peers.refresh.runtime.universe(request()).document() == reviewed
    route = '/v1/releases/' + release.lock.descriptor_sha256
    assert peers.acceptance.registry.read(route, MetadataWindow('registry')) == release
    assert registry_wire.paths == [route, route]
    assert runtime_wire.paths == ['/v1/definition-universe']


@pytest.mark.parametrize('fault', ['actor', 'scope', 'duplicate_id', 'duplicate_path', 'oversized',
    'live_scope', 'live_missing', 'hidden_live', 'fixture', 'eligibility_actor'])
def test_private_configuration_rejects_widening_and_ambiguous_policy(tmp_path, monkeypatch, fault):
    path, config, policy = files(tmp_path, monkeypatch, live=True)
    if fault == 'actor': config['actor_id'] = 'foreign'
    if fault == 'scope': config['scope']['project_id'] = 'foreign'
    if fault == 'duplicate_id':
        config['policies'].append('second.json')
        (tmp_path / 'second.json').write_text(json.dumps(policy), encoding='utf-8')
    if fault == 'duplicate_path': config['policies'].append('policy.json')
    if fault == 'live_scope': config['live']['scope'] = {'tenant_id': 'foreign', 'project_id': 'foreign'}
    if fault == 'live_missing': config.pop('live')
    if fault == 'hidden_live': config['provider'] = 'disabled'
    if fault == 'fixture': config['provider'] = 'fixture_abstain'
    if fault == 'eligibility_actor': config['eligibility']['actor_id'] = 'foreign'
    path.write_text(' ' * 65537 if fault == 'oversized' else json.dumps(config), encoding='utf-8')
    with pytest.raises(ValueError): ReviewedConfiguration.load(path)


def test_disabled_is_default_and_nonlocal_peer_is_rejected(tmp_path, monkeypatch):
    path, config, _ = files(tmp_path, monkeypatch)
    assert WorkerConfiguration.model_validate_json(json.dumps(config)).provider == 'disabled'
    config['data']['endpoint'] = 'https://unreviewed.example'
    path.write_text(json.dumps(config), encoding='utf-8')
    with pytest.raises(ValueError): CurationPeers.bind(ReviewedConfiguration.load(path))


@pytest.mark.postgres
def test_host_check_uses_service_role_without_loading_provider(tmp_path, monkeypatch, planning_database):
    path, _, _ = files(tmp_path, monkeypatch, live=True)
    monkeypatch.setenv('CURATION_TEST_DATABASE', planning_database.render_as_string(hide_password=False))
    host = CurationHost.load(path)
    try:
        assert host.poller.worker.executor.provider is None
        assert host.principal.actions == frozenset({'execute_curations', 'record_requests', 'record_attempts', 'read_attempts'})
        assert host.poller.tick(host.principal) is None
    finally:
        host.close()
    with pytest.raises(KeyError): CurationHost.load(path, enable_provider=True)


@pytest.mark.postgres
def test_separate_process_check_and_disabled_idle_run(tmp_path, monkeypatch, planning_database):
    path, _, _ = files(tmp_path, monkeypatch)
    monkeypatch.setenv('CURATION_TEST_DATABASE', planning_database.render_as_string(hide_password=False))
    base = [sys.executable, '-m', 'amphora_agent_planning.curation_worker']
    for action in ('check', 'run'):
        result = subprocess.run([*base, action, '--config', str(path), '--seconds', '0.1', '--interval', '0.05'],
            capture_output=True, text=True, timeout=45, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert result.returncode == 0, result.stderr
        value = json.loads(result.stdout)
        if action == 'check': assert value == {'status': 'ready', 'mode': 'curation_worker', 'provider_checked': False}
        else: assert value['idle'] >= 1


def test_process_failure_output_does_not_disclose_environment(tmp_path, monkeypatch):
    path, _, _ = files(tmp_path, monkeypatch)
    monkeypatch.setenv('CURATION_TEST_DATABASE', 'secret-marker-not-a-database')
    result = subprocess.run([sys.executable, '-m', 'amphora_agent_planning.curation_worker', 'check', '--config', str(path)],
        capture_output=True, text=True, timeout=45, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert result.returncode == 2 and not result.stdout
    assert 'secret-marker' not in result.stderr and 'Traceback' not in result.stderr
