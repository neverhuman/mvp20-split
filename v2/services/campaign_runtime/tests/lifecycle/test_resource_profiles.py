import pytest
from amphora_campaign_runtime.resource_profiles import InvocationCapacity
from amphora_campaign_runtime.lifecycle.model import RunBudget, TransitionError


def test_legacy_snapshot_never_acquires_configuration_capacity():
    assert InvocationCapacity.from_snapshot({}).available(RunBudget(100, 90, 0))


def test_capacity_counts_unsettled_attempts_rather_than_spent_budget():
    capacity = InvocationCapacity.from_snapshot({"resources": {
        "profile": "campaign-invocation-cap-v1", "max_active_attempts": 4}})
    assert capacity.available(RunBudget(100, 3, 80))
    assert not capacity.available(RunBudget(100, 4, 0))


@pytest.mark.parametrize("resources", [None, {}, {"profile": "future", "max_active_attempts": 4}])
def test_unsupported_snapshot_resources_fail_closed(resources):
    with pytest.raises(TransitionError, match="unsupported_resource_profile"):
        InvocationCapacity.from_snapshot({"resources": resources})
