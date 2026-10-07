import json
from types import SimpleNamespace

import pytest
from amphora_deployment.credentials import SecretBundle
from amphora_deployment.profile import ProfileError
from amphora_deployment.tool_catalog.configuration import load_catalog


def fixture(tmp_path, monkeypatch):
    config = tmp_path / 'worker.json'
    config.write_text(json.dumps({'scope': {'tenant_id': 't', 'project_id': 'p'}, 'actor_id': 'worker'}))
    profile = SimpleNamespace(fingerprint='a' * 64, configuration=config, certificate=tmp_path / 'certificate.pem',
                             name='evolution-seed', image_id='sha256:' + 'b' * 64)
    supervisor = SimpleNamespace(
        scientific=SimpleNamespace(slots={'evolution-seed': SimpleNamespace(binding=SimpleNamespace(profile=profile))}),
        bindings={'registry': SimpleNamespace(port=23456, environment={'AMPHORA_REGISTRY_OPERATOR_TOKEN': 'synthetic-operator-token'})},
        access=SimpleNamespace(bindings={name: SimpleNamespace(port=23457 + index,
            route=SimpleNamespace(upstream_port=23459 + index)) for index, name in enumerate(('runtime', 'artifact'))}))
    monkeypatch.setattr('amphora_deployment.tool_catalog.configuration.worker_credential',
                        lambda *_: SecretBundle({'WORKER_REGISTRY_TOKEN': 'synthetic-heartbeat-token'}))
    record = {'profile': 'local-tool-catalog-v1', 'scope': {'tenant_id': 't', 'project_id': 'p'}, 'worker_id': 'worker',
        'replicas': {'evolution-seed': {'deployment_id': 'seed', 'replica_id': 'slot', 'binding_sha256': 'a' * 64}}}
    path = tmp_path / 'catalog.json'
    path.write_text(json.dumps(record))
    return path, record, supervisor


def test_explicit_configuration_pins_slot_and_keeps_network_off_during_load(tmp_path, monkeypatch):
    path, _, supervisor = fixture(tmp_path, monkeypatch)
    routes = SimpleNamespace(port=lambda _: 23456)
    group = load_catalog(path, tmp_path, 'installation', routes, supervisor)
    assert group.status() == {'evolution-seed': {'state': 'not_started', 'observation': None,
                                              'running': False, 'stopping': False}}
    reporter = group.reporters['evolution-seed']
    assert reporter.journal.binding.replica_id == 'slot'
    assert not reporter.journal.path.exists()
    assert reporter.probe.budget.slots == 1
    assert load_catalog(None, tmp_path, 'installation', routes, supervisor).status() == {}


@pytest.mark.parametrize('change', ['fingerprint', 'scope', 'worker', 'slots', 'route'])
def test_mismatched_catalog_cannot_advertise_for_another_worker(tmp_path, monkeypatch, change):
    path, record, supervisor = fixture(tmp_path, monkeypatch)
    if change == 'fingerprint':
        record['replicas']['evolution-seed']['binding_sha256'] = 'c' * 64
    elif change == 'scope':
        record['scope']['project_id'] = 'other'
    elif change == 'worker':
        record['worker_id'] = 'other'
    elif change == 'slots':
        record['replicas'] = {}
    else:
        supervisor.bindings['registry'].port = 23455
    path.write_text(json.dumps(record))
    with pytest.raises(ProfileError):
        load_catalog(path, tmp_path, 'installation', SimpleNamespace(port=lambda _: 23456), supervisor)
