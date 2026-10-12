from threading import Event
from types import SimpleNamespace

import pytest
from amphora_agent_planning.curation_worker.polling import CurationPoller


def poller():
    result = object.__new__(CurationPoller)
    result.worker_id = 'bounded-worker'
    result.fulfillments, result.fulfillment_turn = None, False
    result.discovery = SimpleNamespace(next=lambda principal: 'original')
    result.worker = SimpleNamespace(tick=lambda *args: args)
    return result


def test_idle_and_selected_identity_are_not_substituted():
    value = poller()
    assert value.tick('principal') == ('principal', 'original', 'bounded-worker')
    value.discovery.next = lambda principal: None
    assert value.tick('principal') is None


def test_stop_is_observed_before_next_job_and_after_bounded_turn():
    value, stop = poller(), Event()
    def tick(principal):
        stop.set()
        return SimpleNamespace(status='pending')
    value.tick = tick
    assert value.sweep(None, seconds=60, interval=60, stop=stop) == {'pending': 1}
    assert value.sweep(None, stop=stop) == {}


@pytest.mark.parametrize('seconds,interval', [(float('nan'), 1), (float('inf'), 1),
    (1, float('nan')), (1, float('inf')), (True, 1), (1, 0), (86401, 1)])
def test_invalid_polling_window_cannot_start_work(seconds, interval):
    with pytest.raises(ValueError, match='curation_polling_window'):
        poller().sweep(None, seconds=seconds, interval=interval)
