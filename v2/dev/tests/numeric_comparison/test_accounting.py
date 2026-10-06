import pytest

from numeric_comparison.accounting import AttemptLedger, compare


def report(costs, limit=None):
    ledger = AttemptLedger(limit or len(costs))
    for cost in costs:
        index = ledger.begin("a" * 64)
        ledger.finish(index, cost=cost, reason="failure" if cost is None else None)
    return ledger.report("budget")


def test_budget_is_charged_before_completion_and_pending_is_not_zero():
    ledger = AttemptLedger(1)
    index = ledger.begin("a" * 64)
    with pytest.raises(ValueError, match="budget"):
        ledger.begin("b" * 64)
    assert ledger.report("interrupted")["failures"] == 1
    assert ledger.report("interrupted")["best_successful_cost"] is None
    ledger.finish(index, cost=0.0)
    with pytest.raises(ValueError, match="already_terminal"):
        ledger.finish(index, cost=1.0)


@pytest.mark.parametrize("cost", [float("nan"), float("inf"), True, "1"])
def test_invalid_numeric_result(cost):
    ledger = AttemptLedger(1)
    index = ledger.begin("a" * 64)
    with pytest.raises(ValueError, match="finite"):
        ledger.finish(index, cost=cost)


def test_metrics_preserve_failure_and_prefix_uncertainty():
    result = report([None, 4.0, 1.0])
    assert result["attempts"] == 3 and result["failures"] == 1
    assert result["best_successful_cost"] == 1.0
    assert result["mean_prefix_best_cost"] is None
    assert report([4.0, 2.0, 3.0])["mean_prefix_best_cost"] == 8 / 3
    assert AttemptLedger(1).report("empty")["best_successful_cost"] is None


@pytest.mark.parametrize("search,baseline,outcome,delta", [
    ([1.0], [2.0], "gain", 1.0), ([2.0], [1.0], "loss", -1.0),
    ([1.0], [1.0], "tie", 0.0), ([None], [1.0], "incomplete", None)])
def test_pair_retains_gains_losses_ties_and_failures(search, baseline, outcome, delta):
    result = compare(report(search), report(baseline))
    assert result["outcome"] == outcome and result["baseline_minus_evolution"] == delta


def test_shortfall_mismatched_allowance_and_transport_failure_are_not_gains():
    assert compare(report([0.0], 2), report([1.0, 2.0]))["outcome"] == "incomplete"
    assert compare(report([0.0]), report([1.0, 2.0]))["outcome"] == "incomplete"
    broken = report([0.0])
    broken["transport_error"] = "failed"
    assert compare(broken, report([1.0]))["outcome"] == "incomplete"


def test_outcome_requires_exactly_success_or_failure():
    ledger = AttemptLedger(1)
    index = ledger.begin("a" * 64)
    for values in ({}, {"cost": 1, "reason": "failed"}):
        with pytest.raises(ValueError, match="outcome"):
            ledger.finish(index, **values)
