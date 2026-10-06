"""Closed numeric capabilities and exact public payload/descriptor publication."""

import json
from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import version

from amphora_contracts_core import SchemaRef
from amphora_contracts_search import SearchCheckpoint, SearchSpec
from amphora_contracts_search_steps import (
    CollectedEvaluations,
    EvaluationRequestBatch,
    SearchStepContext,
)
from amphora_contracts_tools import ReleaseDescriptor

PROFILES = {
    "seed": (SearchSpec, "search.specification", SearchCheckpoint, "search.checkpoint", "Generate one bounded numeric initial population."),
    "requests": (SearchStepContext, "search-step.context", EvaluationRequestBatch, "search-step.requests", "Expand frozen pending identities into evaluator requests."),
    "collect": (CollectedEvaluations, "search-step.collected", SearchCheckpoint, "search.checkpoint", "Reduce the complete frozen result set and select survivors."),
    "vary": (SearchStepContext, "search-step.context", SearchCheckpoint, "search.checkpoint", "Generate one bounded numeric successor population."),
}


@dataclass(frozen=True)
class NumericCapability:
    operation: str

    def __post_init__(self):
        if self.operation not in PROFILES:
            raise ValueError("unsupported_numeric_operation")

    @property
    def release(self):
        return version("amphora-evolution-search")

    @property
    def input_model(self):
        return PROFILES[self.operation][0]

    def schema_bytes(self, direction):
        if direction not in {"input", "output"}:
            raise ValueError("unknown_payload_direction")
        offset = 0 if direction == "input" else 2
        model, name = PROFILES[self.operation][offset:offset + 2]
        schema = model.model_json_schema(mode="validation")
        schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"urn:amphora:{name}:1:validation"})
        return (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()

    def schema_ref(self, direction):
        raw = self.schema_bytes(direction)
        name = PROFILES[self.operation][1 if direction == "input" else 3]
        return SchemaRef(schema_id=name, version="1", sha256=sha256(raw).hexdigest())

    def descriptor(self, image_sha256):
        def port(name, direction):
            return {"name": name, "schema_ref": self.schema_ref(direction).model_dump(mode="json"),
                    "representation": PROFILES[self.operation][1 if direction == "input" else 3], "unit": "1", "required": True}

        data = {
            "schema_version": "1",
            "tool": {"schema_version": "1", "binding": {"capability_id": "numeric.search-" + self.operation,
                     "release": self.release, "image_sha256": image_sha256, "contract_version": "1"},
                     "purpose": PROFILES[self.operation][4], "applicability": ["synthetic-tests", "synthetic-continuous-numeric-search"],
                     "inputs": [port("parameters", "input")], "outputs": [port("result", "output")],
                     "side_effects": "pure", "checkpoint_schema": None},
            "resources": {"architectures": ["x86_64"], "operating_systems": ["linux"], "cpu_millicores": 1000,
                          "memory_mib": 256, "gpu_count": 0, "timeout_seconds": 60,
                          "max_parallel_invocations": 1, "max_batch_size": 1},
            "egress": {"mode": "deny"}, "checkpoint": {"mode": "none", "readable_schema_sha256": []},
            "reproducibility": "deterministic", "authority_ceiling": "synthetic_only",
            "examples": ["One explicit graph step with pinned synthetic numerical inputs."],
            "anti_examples": ["No hidden generation loop, scientific validation or Runtime acceptance."]}
        return ReleaseDescriptor.model_validate_json(json.dumps(data))
