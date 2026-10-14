import pytest

from amphora_contracts_population import EvaluationKey, MethodObservation, UnavailableMethod, EvaluatedMethod, ExecutionPointer, MethodOutput
from amphora_evolution_search.population import BoundEvaluation, FrozenEvaluations, GenerationMembership, frozen_terminal_set


def evaluation(cohort, method_index=0, candidate_index=0):
    original = cohort.original.record
    method = original.method_graph.methods[method_index]
    member = cohort.members[candidate_index]
    key = EvaluationKey(schema_version="1", profile="population-evaluation-key-v1", generation=cohort.identity,
        candidate_id=member.candidate_id, occurrence_id="primary", method_id=method.method_id, tool=method.tool,
        material=member.representation, inputs=(member.representation,), conditions=method.conditions,
        objective_policy_sha256=original.assembly.policy.sha256)
    return BoundEvaluation(cohort, key)


def failed(key):
    return MethodObservation(schema_version="1", profile="population-method-observation-v1",
        key=key.record, evaluation_sha256=key.digest,
        outcome=UnavailableMethod(status="failed", reason_code="exhausted_attempts", producer=None, evidence=()))


def test_named_methods_and_candidates_have_distinct_keys(born_cohort):
    keys = tuple(evaluation(born_cohort, m, c) for m in (0, 1) for c in (0, 1))
    assert len({key.digest for key in keys}) == 4
    frozen = FrozenEvaluations(born_cohort, keys)
    assert frozen.digest == FrozenEvaluations(born_cohort, tuple(reversed(keys))).digest
    with pytest.raises(ValueError, match="required_coverage"):
        FrozenEvaluations(born_cohort, keys[:1])
    observations = tuple(failed(key) for key in keys)
    assert frozen_terminal_set(keys, observations) == frozen_terminal_set(keys, tuple(reversed(observations)))
    assert all(record.outcome.status == "failed" for record in frozen_terminal_set(keys, observations))
    with pytest.raises(ValueError, match="terminal_coverage"):
        frozen_terminal_set(keys, observations[:-1])
    with pytest.raises(ValueError, match="duplicate_or_unknown"):
        frozen_terminal_set(keys, (observations[0],) * 4)


@pytest.mark.parametrize("case,code", [
    ("candidate", "candidate"), ("generation", "generation"), ("method", "method"),
    ("material", "material"), ("tool", "method_pins"), ("policy", "objective_policy"),
    ("duplicate_inputs", "input_duplicate"), ("foreign_input", "input_scope"),
])
def test_cannot_crosswire_evaluation(born_cohort, case, code):
    bound = evaluation(born_cohort); record = bound.record
    if case == "candidate": record = record.model_copy(update={"candidate_id": "f" * 64})
    if case == "generation": record = record.model_copy(update={"generation": record.generation.model_copy(update={"run_id": "other"})})
    if case == "method": record = record.model_copy(update={"method_id": "other"})
    if case == "material": record = record.model_copy(update={"material": born_cohort.members[1].representation})
    if case == "tool": record = record.model_copy(update={"tool": record.tool.model_copy(update={"release": "99.0.0"})})
    if case == "policy": record = record.model_copy(update={"objective_policy_sha256": "f" * 64})
    if case == "duplicate_inputs": record = record.model_copy(update={"inputs": record.inputs * 2})
    if case == "foreign_input":
        extra = record.inputs[0].model_copy(update={"artifact_id": "foreign", "scope": record.generation.scope.model_copy(update={"project_id": "other"})})
        record = record.model_copy(update={"inputs": (*record.inputs, extra)})
    with pytest.raises(ValueError, match="evaluation_" + code):
        BoundEvaluation(born_cohort, record)


def test_actual_result_binding_and_attempt_separation(born_cohort):
    key = evaluation(born_cohort)
    producer = ExecutionPointer(run_id=born_cohort.identity.run_id, activation_id="activation",
        invocation_id="invocation", attempt_id="attempt-one", completion_id="completion")
    output = MethodOutput(port="result", artifact=key.record.material)
    record = MethodObservation(schema_version="1", profile="population-method-observation-v1", key=key.record,
        evaluation_sha256=key.digest, outcome=EvaluatedMethod(status="evaluated", producer=producer, outputs=(output,)))
    assert key.observation(record) == record
    retried = record.model_copy(update={"outcome": record.outcome.model_copy(update={
        "producer": producer.model_copy(update={"attempt_id": "attempt-two"})})})
    assert key.observation(retried).evaluation_sha256 == key.digest
    with pytest.raises(ValueError, match="terminal_coverage"):
        frozen_terminal_set((key,), (record, retried))
    for change, code in [({"run_id": "wrong"}, "producer_run")]:
        bad = record.model_copy(update={"outcome": record.outcome.model_copy(update={"producer": producer.model_copy(update=change)})})
        with pytest.raises(ValueError, match=code): key.observation(bad)
    bad = record.model_copy(update={"outcome": record.outcome.model_copy(update={"outputs": (output, output)})})
    with pytest.raises(ValueError, match="output_duplicate"): key.observation(bad)


def test_empty_frozen_set_keeps_run_and_generation_identity(born_cohort):
    first = GenerationMembership(born_cohort.original, born_cohort.identity, "cohort", ())
    second = GenerationMembership(born_cohort.original, born_cohort.identity.model_copy(update={"run_id": "other"}), "cohort", ())
    assert FrozenEvaluations(first, ()).digest != FrozenEvaluations(second, ()).digest
    assert FrozenEvaluations(first, ()).terminal(()) == ()


def test_input_alias_cannot_replace_a_frozen_condition(born_cohort):
    key = evaluation(born_cohort)
    conflict = key.record.conditions.model_copy(update={"sha256": "f" * 64})
    record = key.record.model_copy(update={"inputs": (*key.record.inputs, conflict)})
    with pytest.raises(ValueError, match="reference_conflict"):
        BoundEvaluation(born_cohort, record)
