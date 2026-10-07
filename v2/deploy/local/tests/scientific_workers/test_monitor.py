import threading
import time
from types import SimpleNamespace

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.scientific_workers.monitor import ScientificSlot


class Binding:
    def __init__(self, phase=None):
        self.phase = phase
        self.journal = SimpleNamespace(read=lambda: None if self.phase is None else {'phase': self.phase})
        self.entered, self.finish = threading.Event(), threading.Event()
        self.launches = 0
        self.releases = 0
        self.fail = False
        self.code = 0

    def turn(self):
        return self

    def launch(self):
        self.launches += 1
        self.phase = 'starting'

    def poll(self):
        self.entered.set()
        assert self.finish.wait(5)
        if self.fail:
            raise OSError('private Docker credentials')
        return self.code

    def release(self):
        self.releases += 1
        self.phase = 'released'


def wait_for(predicate):
    deadline = time.monotonic() + 3
    while not predicate():
        assert time.monotonic() < deadline
        time.sleep(.01)


def test_docker_wait_never_blocks_control_and_quiesce_does_not_interrupt():
    binding = Binding()
    slot = ScientificSlot(binding)
    try:
        slot.start()
        assert binding.entered.wait(2)
        started = time.monotonic()
        assert slot.quiesce()['state'] == 'quiescing'
        assert slot.status()['active_turn']
        assert time.monotonic() - started < .25
        with pytest.raises(ProfileError, match='requires_quiescence'):
            slot.require_quiescent()
        assert binding.releases == 0
        binding.finish.set()
        wait_for(lambda: slot.status()['state'] == 'quiescent')
        slot.require_quiescent()
        assert binding.launches == binding.releases == 1
    finally:
        binding.finish.set()
        slot.detach()


def test_startup_adoption_blocks_shutdown_without_starting_original_again():
    binding = Binding('starting')
    slot = ScientificSlot(binding)
    assert slot.status()['state'] == 'quiescing'
    with pytest.raises(ProfileError, match='requires_quiescence'):
        slot.require_quiescent()
    try:
        slot.adopt()
        assert binding.entered.wait(2)
        assert binding.launches == 0
        binding.finish.set()
        wait_for(lambda: slot.status()['state'] == 'quiescent')
        assert binding.releases == 1
    finally:
        binding.finish.set()
        slot.detach()


def test_uncertain_observation_latches_failure_then_recovery_observes_same_turn():
    binding = Binding()
    binding.fail = True
    slot = ScientificSlot(binding)
    try:
        slot.start()
        assert binding.entered.wait(2)
        binding.finish.set()
        wait_for(lambda: slot.status()['faulted'])
        wait_for(lambda: not slot.thread.is_alive())
        with pytest.raises(ProfileError, match='requires_recovery'):
            slot.start()
        assert 'private' not in str(slot.status())
        binding.fail = False
        slot.recover()
        wait_for(lambda: slot.status()['state'] == 'quiescent')
        assert binding.launches == binding.releases == 1
    finally:
        binding.finish.set()
        slot.detach()


def test_nonzero_exit_is_visible_and_never_repeated_automatically():
    binding = Binding()
    binding.code = 3
    binding.finish.set()
    slot = ScientificSlot(binding)
    try:
        slot.start()
        wait_for(lambda: slot.status()['faulted'])
        assert slot.status()['exit_code'] == 3 and binding.launches == 1
        wait_for(lambda: not slot.thread.is_alive())
        slot.recover()
        assert slot.status()['state'] == 'quiescent'
        slot.require_quiescent()
    finally:
        slot.detach()
