"""Public descriptor and exact published schemas for one isolated operator."""

import hashlib
import json
from importlib.metadata import version

from amphora_contracts_candidate_spaces import ProposedDesignChange, SequenceMoveRequest
from amphora_contracts_core import SchemaRef
from amphora_contracts_tools import ReleaseDescriptor


class SpaceCapability:
    def schema_bytes(self, direction):
        if direction not in {"input", "output"}:
            raise ValueError("unknown_payload_direction")
        model = SequenceMoveRequest if direction == "input" else ProposedDesignChange
        name = (
            "candidate-space.sequence-move"
            if direction == "input"
            else "candidate-space.change"
        )
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
        name = (
            "candidate-space.sequence-move"
            if direction == "input"
            else "candidate-space.change"
        )
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
                    "capability_id": "synthetic.sequence-move",
                    "release": version("amphora-sequence-space"),
                    "image_sha256": image_sha256,
                    "contract_version": "1",
                },
                "purpose": "Propose one legal synthetic sequence representation move.",
                "applicability": ["synthetic-tests", "synthetic-sequence-space"],
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
                "One pinned representation move; source and unknown metadata retained."
            ],
            "anti_examples": [
                "No scientific validity, synthesis decision, registration or hidden loop."
            ],
        }
        return ReleaseDescriptor.model_validate_json(json.dumps(record))
