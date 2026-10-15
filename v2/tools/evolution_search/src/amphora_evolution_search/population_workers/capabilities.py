"""Explicit reference-backed synthetic capabilities; legacy operations unchanged."""

import json
from hashlib import sha256
from dataclasses import dataclass
from importlib.metadata import version

from amphora_contracts_population_steps import (
    PopulationCandidateContext, PopulationMemberSlice, PopulationSliceRequest, PreparedPopulationGeneration,
    SeedPopulationRequest,
)
from amphora_contracts_tools import ReleaseDescriptor
from amphora_contracts_search import ObjectiveValue
from amphora_contracts_core import SchemaRef


from .payloads import CollectPrimaryRequest, CollectedPrimaryGeneration


PROFILES = {
    "collect-primary": (CollectPrimaryRequest, "population-worker.collect-request", CollectedPrimaryGeneration, "population-worker.collected"),
    "seed": (SeedPopulationRequest, "population-step.seed", PreparedPopulationGeneration, "population-step.prepared"),
    "slice": (PopulationSliceRequest, "population-step.slice-request", PopulationMemberSlice, "population-step.member-slice"),
    "evaluate-squares": (PopulationCandidateContext, "population-step.candidate-context", ObjectiveValue, "population-method.objective-value"),
    "evaluate-negative-sum": (PopulationCandidateContext, "population-step.candidate-context", ObjectiveValue, "population-method.objective-value"),
}


@dataclass(frozen=True)
class PopulationCapability:
    operation: str

    def __post_init__(self):
        if self.operation not in PROFILES:
            raise ValueError("unsupported_population_operation")

    @property
    def release(self):
        return version("amphora-evolution-search")

    @property
    def input_model(self):
        return PROFILES[self.operation][0]

    def schema_ref(self, direction):
        if direction not in {"input", "output"}:
            raise ValueError("unknown_payload_direction")
        name = PROFILES[self.operation][1 if direction == "input" else 3]
        return SchemaRef(schema_id=name, version="1", sha256=sha256(self.schema_bytes(direction)).hexdigest())

    def schema_bytes(self, direction):
        if direction not in {"input", "output"}:
            raise ValueError("unknown_payload_direction")
        model, name = PROFILES[self.operation][0:2] if direction == "input" else PROFILES[self.operation][2:4]
        schema = model.model_json_schema(mode="validation")
        schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"urn:amphora:{name}:1:validation"})
        return (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")

    def descriptor(self, image_sha256):
        def port(direction):
            return {"name": "parameters" if direction == "input" else "result",
                    "schema_ref": self.schema_ref(direction).model_dump(),
                    "representation": "population-objective-value-v1" if direction == "output" and self.operation.startswith("evaluate-") else "population-reference-v1",
                    "unit": "1"}
        return ReleaseDescriptor.model_validate_json(json.dumps({"schema_version": "1",
            "tool": {"schema_version": "1", "binding": {"capability_id": "numeric.population-" + self.operation,
                "release": self.release, "image_sha256": image_sha256, "contract_version": "1"},
                "purpose": "Publish one bounded reference-backed synthetic population " + self.operation + " step.",
                "applicability": ["synthetic-numeric-population", "birth-as-representation-v1"],
                "inputs": [port("input")], "outputs": [port("output")], "side_effects": "pure", "checkpoint_schema": None},
            "resources": {"architectures": ["x86_64"], "operating_systems": ["linux"], "cpu_millicores": 1000,
                "memory_mib": 256, "gpu_count": 0, "timeout_seconds": 3600,
                "max_parallel_invocations": 1, "max_batch_size": 1},
            "egress": {"mode": "deny"}, "checkpoint": {"mode": "none", "readable_schema_sha256": []},
            "reproducibility": "deterministic", "authority_ceiling": "synthetic_only",
            "examples": ["A separately admitted step with explicit immutable Artifact ancestry."],
            "anti_examples": ["No hidden scheduler, scientific representation encoder or execution acceptance."]}))
