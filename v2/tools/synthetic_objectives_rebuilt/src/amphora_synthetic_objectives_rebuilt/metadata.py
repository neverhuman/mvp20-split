"""Exact public schemas, fixture policy and image-bound capability descriptor."""

import json
from hashlib import sha256
from importlib.metadata import version

from amphora_contracts_core import SchemaRef
from amphora_contracts_search import EvaluationObservation, EvaluationRequest
from amphora_contracts_tools import ReleaseDescriptor, ToolBinding


def policy_bytes():
    return b'{"profile":"synthetic-quadratic-v1"}'


def tool_binding(image_sha256):
    return ToolBinding(capability_id="synthetic.numeric-objectives", release=version("amphora-synthetic-objectives-rebuilt"),
                       image_sha256=image_sha256, contract_version="1")


def schema_bytes(kind):
    if kind == "policy":
        name = "synthetic.numeric-policy"
        schema = {"type": "object", "additionalProperties": False, "required": ["profile"],
                  "properties": {"profile": {"const": "synthetic-quadratic-v1"}}}
    elif kind in {"input", "output"}:
        model, name = ((EvaluationRequest, "search.evaluation-request") if kind == "input"
                       else (EvaluationObservation, "search.evaluation-observation"))
        schema = model.model_json_schema(mode="validation")
    else:
        raise ValueError("unknown_payload_schema")
    schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"urn:amphora:{name}:1:validation"})
    return (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()


def schema_ref(kind):
    name = {"input": "search.evaluation-request", "output": "search.evaluation-observation", "policy": "synthetic.numeric-policy"}[kind]
    return SchemaRef(schema_id=name, version="1", sha256=sha256(schema_bytes(kind)).hexdigest())


def descriptor(image_sha256):
    def port(name, kind):
        return {"name": name, "schema_ref": schema_ref(kind).model_dump(mode="json"),
                "representation": schema_ref(kind).schema_id, "unit": "1", "required": True}

    data = {
        "schema_version": "1",
        "tool": {"schema_version": "1", "binding": tool_binding(image_sha256).model_dump(mode="json"),
                 "purpose": "Evaluate fixed synthetic quadratic objectives for numerical graph tests.",
                 "applicability": ["synthetic-tests", "synthetic-quadratic-v1", "dimensionless-finite-vectors"],
                 "inputs": [port("parameters", "input"), port("policy", "policy")], "outputs": [port("result", "output")],
                 "side_effects": "pure", "checkpoint_schema": None},
        "resources": {"architectures": ["x86_64"], "operating_systems": ["linux"], "cpu_millicores": 1000,
                      "memory_mib": 128, "gpu_count": 0, "timeout_seconds": 60,
                      "max_parallel_invocations": 1, "max_batch_size": 1},
        "egress": {"mode": "deny"}, "checkpoint": {"mode": "none", "readable_schema_sha256": []},
        "reproducibility": "deterministic", "authority_ceiling": "synthetic_only",
        "examples": ["cost=sum(x_i^2); distance=sum((x_i-1)^2); no hard constraints."],
        "anti_examples": ["No chemistry, biology, synthesis, laboratory, model or scientific-validity claim."]}
    return ReleaseDescriptor.model_validate_json(json.dumps(data))
