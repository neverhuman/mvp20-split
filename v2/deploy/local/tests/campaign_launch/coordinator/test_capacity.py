from datetime import datetime, timedelta, timezone
from threading import RLock
from types import SimpleNamespace

import pytest
from amphora_deployment.campaign_launch.capacity import AdmissionCapacity
from amphora_deployment.campaign_launch.ports import PeerUnavailable


def fixture():
    now = datetime(2026, 10, 9, 14, 30, tzinfo=timezone.utc)
    rows = {'science': {'state': 'quiescent', 'faulted': False, 'active_turn': False}}
    reports = {'science': {'state': 'observed', 'running': True, 'stopping': False,
        'observation': {'free_slots': 1, 'observed_at': now.isoformat(), 'expires_at': (now + timedelta(seconds=15)).isoformat()}}}
    actions = []
    def command(name, action):
        assert action == 'standby'
        rows[name]['state'] = 'standby'; actions.append((name, action))
    supervisor = SimpleNamespace(lock=RLock(), scientific=SimpleNamespace(status=lambda: rows, slots={'science': object()}),
        scientific_command=command, catalog=SimpleNamespace(resume=lambda: actions.append('resume'), status=lambda: reports))
    return AdmissionCapacity(supervisor, now=lambda: now), rows, reports, actions, now


def test_standby_offers_real_capacity_without_starting_scientific_turns():
    capacity, rows, reports, actions, now = fixture()
    capacity.offer(); capacity.offer()
    assert rows['science']['state'] == 'standby'
    assert actions == [('science', 'standby'), 'resume', 'resume']


@pytest.mark.parametrize('mode', ['unobserved', 'zero', 'expired', 'old', 'future', 'stopping', 'missing', 'invalid'])
def test_admission_waits_for_fresh_acknowledged_capacity(mode):
    capacity, rows, reports, actions, now = fixture()
    report = reports['science']; observation = report['observation']
    if mode == 'unobserved': report['state'] = 'unavailable'
    if mode == 'zero': observation['free_slots'] = 0
    if mode == 'expired': observation['expires_at'] = now.isoformat()
    if mode == 'old': observation['observed_at'] = (now - timedelta(seconds=6)).isoformat()
    if mode == 'future': observation['observed_at'] = (now + timedelta(seconds=1)).isoformat()
    if mode == 'stopping': report['stopping'] = True
    if mode == 'missing': reports.clear()
    if mode == 'invalid': observation['observed_at'] = 'bad-time'
    with pytest.raises(PeerUnavailable): capacity.offer()
    assert rows['science']['state'] == 'standby'


@pytest.mark.parametrize('change', [{'state': 'running'}, {'faulted': True}, {'active_turn': True}])
def test_busy_or_unrecovered_workers_are_never_advertised(change):
    capacity, rows, reports, actions, _ = fixture()
    rows['science'].update(change)
    with pytest.raises(PeerUnavailable): capacity.offer()
    assert actions == []
