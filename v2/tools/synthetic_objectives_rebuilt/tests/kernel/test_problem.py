import json
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest
from amphora_contracts_search import (
    EvaluationObservation,
    EvaluationRequest,
    evaluation_observation_schema,
    evaluation_request_schema,
)
from amphora_multi_input_worker import MultiInputToolWorker
from amphora_synthetic_objectives_rebuilt import PolicyBinding, SyntheticProblem
from amphora_synthetic_objectives_rebuilt.adapter import SyntheticWorkerAdapter
from amphora_synthetic_objectives_rebuilt.metadata import (
    descriptor,
    policy_bytes,
    schema_bytes,
    schema_ref,
)
from amphora_tool_protocol import ToolInputRejected
from jsonschema import Draft202012Validator


def test_independent_arithmetic_and_request_identity(worker, fixture_request, bundle):
    result = EvaluationObservation.model_validate_json(worker.execute(bundle))
    assert [(o.objective_id, o.value) for o in result.outcome.objectives] == [("cost", 5.0), ("distance", 9.0)]
    assert result.outcome.quality == "synthetic" and result.outcome.constraint_violation == 0.0
    assert result.outcome.evidence == (bundle["policy"].artifact,)
    canonical = json.dumps(fixture_request.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert result.request_sha256 == sha256(canonical).hexdigest()
    Draft202012Validator(json.loads(schema_bytes("output"))).validate(result.model_dump(mode="json"))


def test_objective_order_and_subsets_are_preserved(worker, fixture_request):
    reversed_request = fixture_request.model_copy(update={"objectives": tuple(reversed(fixture_request.objectives))})
    policy = PolicyBinding(fixture_request.evaluator.constraints, policy_bytes())
    result = SyntheticProblem(reversed_request, worker.binding, policy).evaluate()
    assert [(o.objective_id, o.value) for o in result.outcome.objectives] == [("distance", 9.0), ("cost", 5.0)]
    single = fixture_request.model_copy(update={"objectives": fixture_request.objectives[:1]})
    assert len(SyntheticProblem(single, worker.binding, policy).evaluate().outcome.objectives) == 1


@pytest.mark.parametrize("path,value", [
    (("evaluator", "tool", "image_sha256"), "c" * 64),
    (("evaluator", "tool", "capability_id"), "real-science"),
    (("evaluation_id",), "unbound"),
    (("candidate", "disposition"), "rejected"),
    (("candidate", "genes"), [1000001.0]),
    (("objectives", 0, "objective_id"), "toxicity"),
    (("objectives", 0, "unit"), "kg"),
    (("evaluator", "constraints", "artifact_id"), "undeclared-policy"),
])
def test_inapplicable_or_misbound_requests_reject(worker, fixture_request, path, value):
    data = fixture_request.model_dump(mode="json")
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    altered = EvaluationRequest.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError):
        SyntheticProblem(altered, worker.binding, PolicyBinding(fixture_request.evaluator.constraints, policy_bytes()))


def test_policy_must_be_actual_declared_input_identity(worker, bundle):
    policy = bundle["policy"]
    changed = replace(policy, artifact=policy.artifact.model_copy(update={"artifact_id": "same-bytes-other-artifact"}))
    with pytest.raises(ToolInputRejected, match="invalid_synthetic_objective_input"):
        worker.execute(replace(bundle, inputs=(bundle["parameters"], changed)))


def test_policy_content_schema_and_size_reject(fixture_request):
    with pytest.raises(ValueError, match="synthetic_policy_content"):
        PolicyBinding(fixture_request.evaluator.constraints, b"{}")
    with pytest.raises(ValueError, match="synthetic_policy_binding"):
        PolicyBinding(fixture_request.evaluator.constraints.model_copy(update={"size_bytes": 1}), policy_bytes())


def test_unbound_or_rebound_adapter_rejects(bundle):
    worker = SyntheticWorkerAdapter()
    with pytest.raises(ToolInputRejected):
        worker.execute(bundle)
    worker.descriptor("b" * 64)
    with pytest.raises(ValueError, match="synthetic_worker_image_changed"):
        worker.descriptor("c" * 64)


def test_descriptor_matches_published_contracts_and_multi_input_profile():
    release = descriptor("b" * 64)
    assert "synthetic-tests" in release.tool.applicability
    assert [port.name for port in release.tool.inputs] == ["parameters", "policy"]
    assert schema_ref("input") == evaluation_request_schema()
    assert schema_ref("output") == evaluation_observation_schema()
    peer = SimpleNamespace(identity="fixture")
    MultiInputToolWorker(peer, peer, release, lambda _inputs: b"{}")
    Draft202012Validator(json.loads(schema_bytes("policy"))).validate(json.loads(policy_bytes()))
    with pytest.raises(ValueError, match="unknown_payload_schema"):
        schema_bytes("unknown")
