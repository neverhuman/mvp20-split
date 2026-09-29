"""Exact database-clock boundary and explicit legacy-clock rejection."""

from datetime import UTC, datetime, timedelta

import pytest
from amphora_campaign_runtime.aggregation import CollectionWindow, JoinAccumulator
from amphora_campaign_runtime.lifecycle.model import TransitionError

NOW = datetime(2026, 9, 28, 20, 0, tzinfo=UTC)


def policy(seconds=10):
    return JoinAccumulator({"kind": "partial", "minimum": 0, "close": "deadline", "deadline_seconds": seconds}).policy


def test_deadline_exact_boundary_and_run_clip():
    window = CollectionWindow(NOW, NOW + timedelta(seconds=100))
    assert not window.expired(policy(), NOW + timedelta(seconds=10, microseconds=-1))
    assert window.expired(policy(), NOW + timedelta(seconds=10))
    assert CollectionWindow(NOW, NOW + timedelta(seconds=5)).expired(policy(), NOW + timedelta(seconds=5))


@pytest.mark.parametrize("value", [{"kind": "all"}, {"kind": "partial", "minimum": 0, "close": "all_terminal"}])
def test_non_deadline_policy_does_not_require_legacy_scope_clock(value):
    assert not CollectionWindow(None, None).expired(JoinAccumulator(value).policy, None)


@pytest.mark.parametrize("opened,deadline,now,reason", [
    (None, NOW, NOW, "aggregate_clock_unavailable"),
    (NOW.replace(tzinfo=None), NOW, NOW, "timezone_required"),
    (NOW, NOW, NOW, "aggregate_clock_invalid"),
    (NOW, NOW + timedelta(seconds=1), NOW.replace(tzinfo=None), "timezone_required"),
])
def test_invalid_clock_is_explicit(opened, deadline, now, reason):
    with pytest.raises(TransitionError, match=reason):
        CollectionWindow(opened, deadline).expired(policy(), now)
