import json
from hashlib import sha256

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_search import EvaluationRequest
from amphora_multi_input_worker import InputBundle, ResolvedInput
from amphora_synthetic_objectives_rebuilt.adapter import SyntheticWorkerAdapter
from amphora_synthetic_objectives_rebuilt.metadata import policy_bytes, schema_ref

IMAGE = "b" * 64  # Descriptor fixture, not evidence of a built image.


@pytest.fixture
def worker():
    adapter = SyntheticWorkerAdapter()
    adapter.descriptor(IMAGE)
    return adapter


@pytest.fixture
def fixture_request(worker):
    scope = {"tenant_id": "fixture", "project_id": "synthetic-objectives"}
    raw = policy_bytes()
    policy = {"artifact_id": "synthetic-policy", "scope": scope, "sha256": sha256(raw).hexdigest(),
              "size_bytes": len(raw), "media_type": "application/json", "schema_ref": schema_ref("policy").model_dump(mode="json")}
    return EvaluationRequest.model_validate_json(json.dumps({
        "schema_version": "1", "scope": scope, "evaluation_id": "ev-" + "a" * 64, "specification_sha256": "f" * 64,
        "candidate": {"candidate_id": "a" * 64, "generation": 0, "ordinal": 0, "operator": "seed", "genes": [1.0, -2.0],
                      "parents": [], "draws": {"start": 0, "end": 2}, "disposition": "proposed", "reason_code": None, "duplicate_of": None},
        "objectives": [{"objective_id": "cost", "unit": "dimensionless", "direction": "minimize"},
                       {"objective_id": "distance", "unit": "dimensionless", "direction": "maximize"}],
        "evaluator": {"tool": worker.binding.model_dump(mode="json"), "constraints": policy, "context": [],
                      "completion": "all_frozen_members_terminal"}}))


@pytest.fixture
def bundle(fixture_request):
    raw = fixture_request.model_dump_json().encode()
    reference = ArtifactRef(artifact_id="fixture_request-fixture", scope=fixture_request.scope, sha256=sha256(raw).hexdigest(),
                            size_bytes=len(raw), media_type="application/json", schema_ref=schema_ref("input"))
    return InputBundle((ResolvedInput("parameters", reference, raw),
                        ResolvedInput("policy", fixture_request.evaluator.constraints, policy_bytes())))
