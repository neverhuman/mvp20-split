import json
from pathlib import Path

import pytest
from amphora_contracts_search_steps import (
    CollectedEvaluations,
    EvaluationRequestBatch,
    SearchStepContext,
)
from jsonschema import Draft202012Validator

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def context():
    checkpoint = json.loads((FIXTURES / "checkpoint.json").read_bytes())
    return {"original_specification": checkpoint["specification"], "checkpoint": checkpoint,
            "checkpoint_artifact": checkpoint["specification"]["evaluator"]["constraints"]}


@pytest.mark.parametrize("model", [SearchStepContext, CollectedEvaluations])
def test_context_wire_roundtrip_does_not_confer_checkpoint_authority(context, model):
    if model is CollectedEvaluations:
        context["results"] = [{"kind": "missing", "reason_code": "tool_failed", "member_id": "0"}]
    record = model.model_validate_json(json.dumps(context))
    assert model.model_validate_json(record.model_dump_json()) == record
    for mode in ("validation", "serialization"):
        Draft202012Validator(model.model_json_schema(mode=mode)).validate(context)


def test_request_batch_uses_actual_public_request_shape(context):
    request = json.loads((FIXTURES / "request.json").read_bytes())
    data = {"schema_version": "1", "scope": request["scope"],
            "specification_sha256": request["specification_sha256"],
            "checkpoint_artifact": context["checkpoint_artifact"], "requests": [request]}
    batch = EvaluationRequestBatch.model_validate_json(json.dumps(data))
    assert batch.requests[0].candidate.candidate_id == request["candidate"]["candidate_id"]
    Draft202012Validator(EvaluationRequestBatch.model_json_schema()).validate(data)


@pytest.mark.parametrize("case", ["extra_authority", "missing_identity", "unbounded_results", "missing_with_fitness"])
def test_closed_collected_shape(context, case):
    context["results"] = [{"kind": "missing", "reason_code": "tool_failed", "member_id": "0"}]
    if case == "extra_authority":
        context["accepted"] = True
    elif case == "missing_identity":
        del context["results"][0]["member_id"]
    elif case == "unbounded_results":
        context["results"] *= 129
    else:
        context["results"][0]["objectives"] = [0.0]
    with pytest.raises(ValueError):
        CollectedEvaluations.model_validate_json(json.dumps(context))
