"""Independent rejection and numeric-edge oracles for the rebuilt implementation."""

import json
from dataclasses import replace

import pytest
from amphora_contracts_search import EvaluationRequest
from amphora_multi_input_worker import InputBundle, ResolvedInput
from amphora_synthetic_objectives_rebuilt import PolicyBinding, SyntheticProblem
from amphora_synthetic_objectives_rebuilt.metadata import policy_bytes
from amphora_tool_protocol import ToolInputRejected


@pytest.mark.parametrize("genes,cost,distance", [
    ([0.0], 0.0, 1.0), ([1.0] * 32, 32.0, 0.0),
    ([-1000000.0, 1000000.0], 2000000000000.0, 2000000000002.0),
    ([0.5, -0.5], 0.5, 2.5),
])
def test_numeric_edges(worker, fixture_request, genes, cost, distance):
    data = fixture_request.model_dump(mode="json")
    data["candidate"]["genes"] = genes
    request = EvaluationRequest.model_validate_json(json.dumps(data))
    result = SyntheticProblem(request, worker.binding,
                              PolicyBinding(request.evaluator.constraints, policy_bytes())).evaluate()
    assert [item.value for item in result.outcome.objectives] == [cost, distance]


@pytest.mark.parametrize("kind", ["context", "duplicates", "old_release", "scope", "nan", "inf"])
def test_additional_applicability_rejects(worker, fixture_request, kind):
    data = fixture_request.model_dump(mode="json")
    if kind == "context":
        data["evaluator"]["context"] = [data["evaluator"]["constraints"]]
    elif kind == "duplicates":
        data["objectives"] *= 2
    elif kind == "old_release":
        data["evaluator"]["tool"]["release"] = "0.3.0"
    elif kind == "scope":
        data["scope"]["project_id"] = "another-scope"
    else:
        data["candidate"]["genes"] = [float(kind)]
    with pytest.raises(ValueError):
        request = EvaluationRequest.model_validate_json(json.dumps(data))
        SyntheticProblem(request, worker.binding,
                         PolicyBinding(request.evaluator.constraints, policy_bytes()))


def test_unexpected_port_rejects_safely(worker, bundle):
    unexpected = replace(bundle["parameters"], port="unexpected")
    with pytest.raises(ToolInputRejected, match="invalid_synthetic_objective_input"):
        worker.execute(InputBundle((unexpected, bundle["policy"])))


@pytest.mark.parametrize("field,value", [
    ("sha256", "0" * 64), ("media_type", "text/plain"),
])
def test_policy_metadata_rejects(fixture_request, field, value):
    reference = fixture_request.evaluator.constraints.model_copy(update={field: value})
    with pytest.raises(ValueError, match="synthetic_policy_binding"):
        PolicyBinding(reference, policy_bytes())


def test_invalid_parameters_reject_without_echo(worker, bundle):
    from hashlib import sha256
    body = b"private-invalid-fixture"
    reference = bundle["parameters"].artifact.model_copy(update={"size_bytes": len(body), "sha256": sha256(body).hexdigest()})
    changed = InputBundle((ResolvedInput("parameters", reference, body), bundle["policy"]))
    with pytest.raises(ToolInputRejected, match="^invalid_synthetic_objective_input$"):
        worker.execute(changed)
