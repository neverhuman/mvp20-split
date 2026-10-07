from types import SimpleNamespace

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.scientific_workers.monitor import ScientificSlot
from amphora_deployment.tool_catalog.availability import (
    CapacityObservation,
    CapacityProbe,
    ExecutorBudget,
)


class Engine:
    def __init__(self):
        self.cpus = 10
        self.memory = 5 * 1024**3
        self.failed = False
        self.images = []

    def verify_image(self, profile):
        self.images.append(profile)
        if self.failed:
            raise OSError('private details')

    def resources(self):
        return {'cpus': self.cpus, 'memory': self.memory}


def setup_probe():
    binding = SimpleNamespace(journal=SimpleNamespace(read=lambda: None), profile=SimpleNamespace(verify=lambda: None))
    slot = ScientificSlot(binding)
    engine = Engine()
    return slot, engine, CapacityProbe(slot, ExecutorBudget(5), lambda: True, engine=engine)


def test_no_capacity_without_explicit_offer_and_fresh_complete_observation():
    slot, engine, probe = setup_probe()
    assert not probe.observe().available and not engine.images
    slot.standby()
    observed = probe.observe()
    assert observed.available and observed.fresh() and len(engine.images) == 1
    assert observed.reason == 'verified_local_executor'
    assert not observed.fresh(observed.checked_at + 5.01)
    assert not observed.fresh(observed.checked_at - .01)
    assert not CapacityObservation(False, observed.checked_at, 'unavailable').fresh()


@pytest.mark.parametrize('phase', ['intent', 'created', 'starting', 'started', 'exited'])
def test_prepared_or_ambiguous_turn_cannot_advertise_capacity(phase):
    slot, _, probe = setup_probe()
    slot.standby()
    slot.binding.journal.read = lambda: {'phase': phase}
    assert probe.observe().reason == 'unresolved_container_turn'


def test_missing_resource_failed_image_or_unavailable_dependencies_withdraw_capacity():
    slot, engine, probe = setup_probe()
    slot.standby()
    engine.cpus = 9
    assert probe.observe().reason == 'executor_budget_unavailable'
    engine.cpus, engine.memory = 10, 1024**3
    assert probe.observe().reason == 'executor_budget_unavailable'
    engine.memory, engine.failed = 5 * 1024**3, True
    assert probe.observe().reason == 'observation_unavailable'
    assert 'private' not in str(probe.observe())
    engine.failed = False
    probe.dependencies = lambda: False
    assert probe.observe().reason == 'dependencies_unavailable'


def test_quiesce_during_slow_dependency_check_invalidates_positive_observation():
    slot, _, probe = setup_probe()
    slot.standby()
    def dependencies():
        slot.quiesce()
        return True
    probe.dependencies = dependencies
    assert probe.observe().reason == 'slot_not_offering'


@pytest.mark.parametrize('slots', [0, 6, True, 1.5])
def test_executor_budget_must_match_closed_slot_bound(slots):
    with pytest.raises(ProfileError):
        ExecutorBudget(slots)
