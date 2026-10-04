"""Family-budget iteration using scripted published Artifacts and actual owned SQL."""

from types import SimpleNamespace

import pytest
from amphora_agent_planning.repair.chain import RepairChain, RepairInputs
from amphora_agent_planning.repair.feedback import RepairFeedback
from amphora_agent_planning.repair.history import RepairHistory
from amphora_agent_planning.repair.preparation import RepairPreparer
from amphora_agent_planning.repair.runner import RepairInputUnavailable, RepairRunner
from amphora_contracts_core import Finding

from ..repair.support import references
from .test_preparation import enrolled
from .test_repair_runner import Provider

pytestmark = pytest.mark.postgres


class Producer:
    def __init__(self, s, root, data):
        self.s, self.root, self.data, self.calls = s, root, data, 0

    def next(self, step):
        self.calls += 1
        history = RepairHistory.read(self.s.engine, self.s.principal, self.root, step.trace.reference())
        feedback = RepairFeedback.create(history.task, history.projection, history.observation,
            (Finding(code="invalid_output", location="/", message="Repair syntax while retaining earlier work"),), prior=history.prior)
        value = SimpleNamespace(task=history.task, feedback=feedback, projection=history.projection)
        f, i = references(value)
        f = f.model_copy(update={"artifact_id": "feedback-" + str(self.calls)})
        i = i.model_copy(update={"artifact_id": "interpretation-" + str(self.calls)})
        for ref, body in ((f, feedback.canonical), (i, history.projection.canonical)):
            self.data.artifacts[ref.artifact_id] = ref
            self.data.payloads[ref.artifact_id] = body
        return RepairInputs(history.projection.reference(), f, i)


def test_chain_exhausts_original_budget_and_retains_prior_steps(stored):
    s = stored
    prepared, data, knowledge = enrolled(s, return_fixture=True)
    root = prepared.history.root.task.document().engagement
    provider = Provider()
    runner = RepairRunner(s.engine, RepairPreparer(data, knowledge), provider, timeout_seconds=10)
    producer = Producer(s, root, data)
    initial = RepairInputs(prepared.history.projection.reference(), prepared.plan.feedback_reference(),
                           prepared.plan.interpretation_reference())
    result = RepairChain(runner, producer).run(s.principal, root, initial)
    assert result.stop_reason == "repair_attempt_budget_exhausted"
    assert len(provider.packets) == prepared.history.root.task.request.document().context.limits.max_attempts - 1
    assert result.steps[0].trace.document().prior == initial.parent
    assert result.steps[-1].attempt is None and result.steps[-1].trace is None
    assert all(step.trace is not None for step in result.steps[:-1])


def test_producer_can_finish_with_partial_useful_history(stored):
    s = stored
    prepared, data, knowledge = enrolled(s, return_fixture=True)
    class Finished:
        def next(self, step):
            assert step.trace is not None
            return None
    runner = RepairRunner(s.engine, RepairPreparer(data, knowledge), Provider(), timeout_seconds=10)
    result = RepairChain(runner, Finished()).run(s.principal, prepared.history.root.task.document().engagement,
        RepairInputs(prepared.history.projection.reference(), prepared.plan.feedback_reference(), prepared.plan.interpretation_reference()))
    assert result.stop_reason == "repair_complete"
    assert len(result.steps) == 1
    assert result.steps[0].attempt.observation.capture.content == b"{"


@pytest.mark.parametrize("boundary", ["producer", "reader"])
def test_later_input_unavailability_retains_completed_step(stored, boundary):
    s = stored
    prepared, data, knowledge = enrolled(s, return_fixture=True)
    root = prepared.history.root.task.document().engagement
    provider = Provider()
    class Unavailable(Producer):
        def next(self, step):
            if boundary == "producer":
                raise RepairInputUnavailable("diagnostics_unavailable")
            following = super().next(step)
            self.data.payloads[following.feedback.artifact_id] = b"wrong bytes"
            return following
    runner = RepairRunner(s.engine, RepairPreparer(data, knowledge), provider, timeout_seconds=10)
    result = RepairChain(runner, Unavailable(s, root, data)).run(s.principal, root,
        RepairInputs(prepared.history.projection.reference(), prepared.plan.feedback_reference(), prepared.plan.interpretation_reference()))
    assert result.stop_reason == ("diagnostics_unavailable" if boundary == "producer" else "source_artifact_bytes")
    assert len(result.steps) == len(provider.packets) == 1
    assert result.steps[0].trace is not None
