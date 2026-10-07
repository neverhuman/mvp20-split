import threading
import time
from types import SimpleNamespace

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.tool_catalog.availability import CapacityObservation
from amphora_deployment.tool_catalog.reporter import CapacityReporter

from .test_heartbeat import journal, receipt


class Probe:
    def __init__(self):
        self.ready = True
        self.slot = SimpleNamespace(offers_capacity=lambda: self.ready)

    def observe(self):
        return CapacityObservation(self.ready, time.monotonic(), 'fixture')


def test_no_advertisement_without_readiness_and_zero_after_quiesce(tmp_path):
    probe, commands = Probe(), []
    def send(command):
        commands.append(command)
        return receipt(command)
    reporter = CapacityReporter(probe, journal(tmp_path), SimpleNamespace(send=send))
    probe.ready = False
    reporter._report()
    assert not commands and reporter.status()['state'] == 'unavailable'
    probe.ready = True
    reporter._report()
    assert commands[-1]['payload']['free_slots'] == 1
    probe.ready = False
    reporter._report()
    assert commands[-1]['payload']['free_slots'] == 0
    assert reporter.status()['observation']['revision'] == 2


def test_uncertain_positive_is_not_replayed_on_shutdown_or_unready_restart(tmp_path):
    probe, commands = Probe(), []
    def failed(command):
        commands.append(command)
        raise OSError('private credential')
    reporter = CapacityReporter(probe, journal(tmp_path), SimpleNamespace(send=failed))
    reporter._report()
    assert 'private' not in str(reporter.status())
    reporter._report(closing=True)
    assert len(commands) == 1 and reporter.status()['state'] == 'uncertain_waiting_for_fresh_readiness'
    probe.ready = False
    replacement = CapacityReporter(probe, journal(tmp_path), SimpleNamespace(send=lambda command: receipt(command)))
    replacement._report()
    assert replacement.status()['state'] == 'uncertain_waiting_for_fresh_readiness'
    probe.ready = True
    replacement._report()
    assert replacement.status()['observation']['revision'] == 1
    assert journal(tmp_path).read()['pending'] is None


def test_background_delivery_never_holds_status_lock_and_finally_withdraws(tmp_path):
    entered, finish = threading.Event(), threading.Event()
    commands = []
    def send(command):
        commands.append(command)
        if len(commands) == 1:
            entered.set()
            assert finish.wait(3)
        return receipt(command)
    reporter = CapacityReporter(Probe(), journal(tmp_path), SimpleNamespace(send=send))
    try:
        reporter.start()
        reporter.start()
        assert entered.wait(2)
        started = time.monotonic()
        reporter.quiesce()
        assert reporter.status()['running'] and reporter.status()['stopping']
        assert time.monotonic() - started < .25
        with pytest.raises(ProfileError, match='requires_drain'):
            reporter.require_stopped()
        finish.set()
        reporter.close()
        assert [c['payload']['free_slots'] for c in commands] == [1, 0]
        assert reporter.status()['observation']['revision'] == 2
        assert not reporter.status()['running']
        with pytest.raises(ProfileError, match='closed'):
            reporter.start()
    finally:
        finish.set()
        reporter.close()


def test_stopped_reporter_resumes_same_replica_and_revision_after_registry_restart(tmp_path):
    commands = []
    observed = threading.Event()
    def send(command):
        commands.append(command)
        observed.set()
        return receipt(command)
    probe = Probe()
    reporter = CapacityReporter(probe, journal(tmp_path), SimpleNamespace(send=send))
    try:
        reporter.start()
        assert observed.wait(2)
        reporter.close()
        prior = journal(tmp_path).read()['revision']
        observed.clear()
        probe.ready = False
        reporter.resume()
        assert observed.wait(2)
        reporter.close()
        assert journal(tmp_path).read()['revision'] > prior
        assert {command['payload']['replica_id'] for command in commands} == {'seed-slot'}
    finally:
        reporter.close()
