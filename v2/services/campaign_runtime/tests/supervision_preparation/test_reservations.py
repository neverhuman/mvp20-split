"""Independent potential-call ceiling and replay oracles."""

from dataclasses import FrozenInstanceError

import pytest
from amphora_campaign_runtime.supervision_preparation import (
    CallReservations,
    RequestCharge,
)

from ..supervision_policy.support import plan, policy


def reserve(history, charge, *, slot_requests=2, slot_calls=4, campaign_requests=20, campaign_calls=30):
    record = policy(plan())
    rule = record.checkpoints[0].model_copy(update={'max_requests': slot_requests, 'max_model_calls': slot_calls})
    ceilings = record.ceilings.model_copy(update={'max_requests': campaign_requests, 'max_model_calls': campaign_calls})
    return history.reserve(charge, rule=rule, ceilings=ceilings)


def test_full_allowance_reserved_once_with_no_mutation_or_refund():
    original = CallReservations()
    charge = RequestCharge('a' * 64, 'b' * 64, 2)
    first = reserve(original, charge)
    assert original.charges == () and first.charges == (charge,)
    assert reserve(first, charge, slot_requests=1, slot_calls=2) is first
    second = reserve(first, RequestCharge('a' * 64, 'c' * 64, 2))
    assert sum(item.max_attempts for item in second.charges) == 4
    with pytest.raises(FrozenInstanceError):
        charge.max_attempts = 1


@pytest.mark.parametrize('limits,decision,reason', [
    ({'slot_requests': 1}, 'a', 'slot_requests'),
    ({'campaign_requests': 1}, 'c', 'campaign_requests'),
    ({'slot_calls': 3}, 'a', 'slot_calls'),
    ({'campaign_calls': 3}, 'c', 'campaign_calls'),
])
def test_each_original_ceiling(limits, decision, reason):
    history = CallReservations((RequestCharge('a' * 64, 'b' * 64, 2),))
    with pytest.raises(ValueError, match=reason):
        reserve(history, RequestCharge(decision * 64, 'd' * 64, 2), **limits)
    assert len(history.charges) == 1


@pytest.mark.parametrize('decision,attempts', [('c', 2), ('a', 1)])
def test_replay_cannot_change_slot_or_attempt_allowance(decision, attempts):
    history = CallReservations((RequestCharge('a' * 64, 'b' * 64, 2),))
    with pytest.raises(ValueError, match='replay_conflict'):
        reserve(history, RequestCharge(decision * 64, 'b' * 64, attempts))


@pytest.mark.parametrize('attempts', [0, 17, True, 2.0])
def test_strict_attempt_allowance(attempts):
    with pytest.raises(ValueError, match='reservation_attempts'):
        RequestCharge('a' * 64, 'b' * 64, attempts)


def test_history_and_identity_cannot_be_ambiguous():
    charge = RequestCharge('a' * 64, 'b' * 64, 2)
    for history in ([charge], (object(),)):
        with pytest.raises(ValueError, match='reservation_history'):
            CallReservations(history)
    with pytest.raises(ValueError, match='duplicate_request'):
        CallReservations((charge, charge))
    with pytest.raises(ValueError, match='invalid_digest'):
        RequestCharge('bad', 'b' * 64, 2)
    with pytest.raises(ValueError, match='reservation_charge'):
        reserve(CallReservations(), object())
