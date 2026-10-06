"""Public descriptor and exact published schemas for one isolated operator."""

import hashlib
import json
from importlib.metadata import version

from amphora_contracts_candidate_spaces import PolymerDesign, PolymerMoveRequest, ProposedDesignChange
from amphora_contracts_candidate_canonicalization import CanonicalCandidate
from amphora_contracts_core import SchemaRef
from amphora_contracts_tools import ReleaseDescriptor


class SpaceCapability:
    def __init__(self, operation="move"):
        if operation not in {"move", "canonicalize"}:
            raise ValueError("unknown_space_operation")
        self.operation = operation

    def schema_name(self, direction):
        if direction not in {"input", "output"}:
            raise ValueError("unknown_payload_direction")
        if self.operation == "canonicalize":
            return "candidate-space.polymer" if direction == "input" else "candidate-canonicalization.receipt"
        return "candidate-space.polymer-move" if direction == "input" else "candidate-space.change"

    def schema_bytes(self, direction):
        if direction not in {"input", "output"}:
            raise ValueError("unknown_payload_direction")
        if self.operation == "canonicalize":
            model = PolymerDesign if direction == "input" else CanonicalCandidate
        else:
            model = PolymerMoveRequest if direction == "input" else ProposedDesignChange
        name = self.schema_name(direction)
        schema = model.model_json_schema(mode="validation")
        schema.update(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": f"urn:amphora:{name}:1:validation",
            }
        )
        return (
            json.dumps(
                schema,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")

    def schema_ref(self, direction):
        raw = self.schema_bytes(direction)
        name = self.schema_name(direction)
        return SchemaRef(
            schema_id=name, version="1", sha256=hashlib.sha256(raw).hexdigest()
        )

    def descriptor(self, image_sha256):
        def port(name, direction):
            reference = self.schema_ref(direction)
            return {
                "name": name,
                "schema_ref": reference.model_dump(mode="json"),
                "representation": reference.schema_id,
                "unit": "1",
                "required": True,
            }

        record = {
            "schema_version": "1",
            "tool": {
                "schema_version": "1",
                "binding": {
                    "capability_id": "synthetic.polymer-" + self.operation,
                    "release": version("amphora-polymer-space"),
                    "image_sha256": image_sha256,
                    "contract_version": "1",
                },
                "purpose": ("Canonicalize one synthetic polymer design with source-byte provenance." if self.operation == "canonicalize" else "Propose one legal synthetic polymer representation move."),
                "applicability": ["synthetic-tests", "synthetic-polymer-space"],
                "inputs": [port("parameters", "input")],
                "outputs": [port("result", "output")],
                "side_effects": "pure",
                "checkpoint_schema": None,
            },
            "resources": {
                "architectures": ["x86_64"],
                "operating_systems": ["linux"],
                "cpu_millicores": 1000,
                "memory_mib": 256,
                "gpu_count": 0,
                "timeout_seconds": 60,
                "max_parallel_invocations": 1,
                "max_batch_size": 1,
            },
            "egress": {"mode": "deny"},
            "checkpoint": {"mode": "none", "readable_schema_sha256": []},
            "reproducibility": "deterministic",
            "authority_ceiling": "synthetic_only",
            "examples": [
                "One pinned representation operation; source and unknown metadata retained."
            ],
            "anti_examples": [
                "No scientific validity, synthesis decision, registration or hidden loop."
            ],
        }
        return ReleaseDescriptor.model_validate_json(json.dumps(record))
