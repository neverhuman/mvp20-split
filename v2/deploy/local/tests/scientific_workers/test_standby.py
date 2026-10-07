from types import SimpleNamespace

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.scientific_workers.monitor import ScientificSlot


def test_explicit_standby_never_launches_work_and_must_quiesce_before_api_drain():
    slot = ScientificSlot(SimpleNamespace(journal=SimpleNamespace(read=lambda: None)))
    assert not slot.offers_capacity()
    assert slot.standby()['state'] == 'standby'
    assert slot.offers_capacity() and slot.thread is None
    assert slot.standby()['state'] == 'standby'
    with pytest.raises(ProfileError, match='requires_quiescence'):
        slot.require_quiescent()
    slot.quiesce()
    assert not slot.offers_capacity()
    slot.require_quiescent()
    slot.detach()
    with pytest.raises(ProfileError, match='requires_idle'):
        slot.standby()


@pytest.mark.parametrize('flag', ['active', 'faulted', 'enabled', 'closing'])
def test_standby_cannot_bypass_running_failed_or_closed_slot(flag):
    slot = ScientificSlot(SimpleNamespace(journal=SimpleNamespace(read=lambda: None)))
    setattr(slot, flag, True)
    with pytest.raises(ProfileError, match='requires_idle'):
        slot.standby()


def test_capacity_offer_is_withdrawn_by_failure_or_accepted_work():
    slot = ScientificSlot(SimpleNamespace(journal=SimpleNamespace(read=lambda: None)))
    slot.standby()
    for flag in ('active', 'faulted', 'closing'):
        setattr(slot, flag, True)
        assert not slot.offers_capacity()
        setattr(slot, flag, False)
    assert slot.offers_capacity()
