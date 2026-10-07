import copy
from types import SimpleNamespace

import pytest
from amphora_deployment.tool_catalog.heartbeat import ReplicaBinding
from amphora_deployment.tool_catalog.target import CatalogTarget


def target():
    replica = ReplicaBinding('installation', 'internal', 'demo', 'worker', 'seed', 'slot')
    profile = SimpleNamespace(name='evolution-seed', image_id='sha256:' + 'a' * 64)
    return CatalogTarget(replica, profile, 23456, 'synthetic-operator-token')


def snapshot():
    return {'scope': {'tenant_id': 'internal', 'project_id': 'demo'}, 'status': 'active', 'deployment': {
        'deployment_id': 'seed', 'architecture': 'x86_64', 'operating_system': 'linux', 'workers': ['worker'],
        'release': {'tool': {'capability_id': 'numeric.search-seed', 'image_sha256': 'a' * 64,
                             'contract_version': '1'}}}}


def test_rebuilt_catalog_profile_requires_its_exact_image():
    probe, value = target(), snapshot()
    probe.profile.name = 'synthetic-objectives-rebuilt'
    value['deployment']['release']['tool']['capability_id'] = 'synthetic.numeric-objectives'
    assert probe.matches(value)
    value['deployment']['release']['tool']['image_sha256'] = 'b' * 64
    assert not probe.matches(value)


@pytest.mark.parametrize(('path', 'bad'), [
    (('scope', 'project_id'), 'other'), (('status',), 'draining'),
    (('deployment', 'deployment_id'), 'other'), (('deployment', 'architecture'), 'aarch64'),
    (('deployment', 'operating_system'), 'windows'), (('deployment', 'workers'), ['other']),
    (('deployment', 'release', 'tool', 'image_sha256'), 'b' * 64),
    (('deployment', 'release', 'tool', 'capability_id'), 'numeric.search-vary'),
    (('deployment', 'release', 'tool', 'contract_version'), '2'),
    (('deployment', 'release'), None), (('deployment',), None),
])
def test_catalog_target_rejects_foreign_or_incompatible_deployment(path, bad):
    probe, value = target(), snapshot()
    assert probe.matches(value)
    altered = copy.deepcopy(value)
    part = altered
    for key in path[:-1]:
        part = part[key]
    part[path[-1]] = bad
    assert not probe.matches(altered)
    assert not probe.matches(None)
    assert 'synthetic-operator-token' not in repr(probe)
