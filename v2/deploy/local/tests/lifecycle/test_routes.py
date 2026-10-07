import os

import pytest

from amphora_deployment.lifecycle.routes import Routes, NAMES
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.profile import ProfileError


@pytest.mark.skipif(os.name != 'nt', reason='Selected Windows profile')
def test_routes_require_persistence_and_resume_without_reallocation(tmp_path):
    with pytest.raises(ProfileError, match='stores_required'):
        Routes.ensure(tmp_path)
    with LocalState(tmp_path) as state:
        state.record['phase'] = 'stores_ready'
        state.save()
    first = Routes.ensure(tmp_path)
    assert len(set(port for _, port in first.ports)) == len(NAMES)
    assert Routes.ensure(tmp_path) == first
    with LocalState(tmp_path):
        assert Routes.load(tmp_path) == first  # Status must not compete for the writer lock.
    assert all(first.endpoint(name).startswith('http://127.0.0.1:') for name in NAMES)


@pytest.mark.parametrize('change', ['host', 'unknown', 'duplicate', 'boolean'])
def test_routes_reject_unsafe_or_ambiguous_endpoints(change):
    record = {'profile':'loopback-routes-v1', 'host':'127.0.0.1', 'ports':{name:18000+i for i,name in enumerate(NAMES)}}
    if change == 'host': record['host'] = '0.0.0.0'
    elif change == 'unknown': record['ports']['unreviewed'] = 19000
    elif change == 'duplicate': record['ports'][NAMES[1]] = record['ports'][NAMES[0]]
    else: record['ports'][NAMES[0]] = True
    with pytest.raises(ProfileError): Routes.from_record(record)
