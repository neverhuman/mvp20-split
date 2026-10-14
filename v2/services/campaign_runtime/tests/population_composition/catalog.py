"""Compile-only synthetic descriptors; no claim that these tool workers exist."""

import hashlib
import json

from amphora_contracts_core import ArtifactRef
from amphora_contracts_tools import LockEntry, ReleaseDescriptor
from amphora_campaign_runtime.compiler import PinnedSchema, ResolvedTool, SchemaCatalog, SchemaIdentity, ToolCatalog


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


class CompositionCatalog:
    def __init__(self, batch):
        artifact = ArtifactRef.model_json_schema()
        reference = {k: v for k, v in artifact.items() if k != "$defs"}
        missing = {"type": "object", "required": ["kind", "member_id", "reason_code"],
                   "properties": {"kind": {"const": "missing"}, "member_id": {"type": "string"},
                                  "reason_code": {"type": "string"}}}
        state = {"type": "object", "required": ["members", "slice_complete", "campaign_stopped"],
                 "properties": {"members": {"type": "array", "maxItems": batch, "items": reference},
                                "slice_complete": {"type": "boolean"}, "campaign_stopped": {"type": "boolean"}}}
        collected = {"type": "object", "required": ["state", "results"],
                     "properties": {"state": reference, "results": {"type": "array", "maxItems": max(2, batch),
                                     "items": {"anyOf": [reference, missing]}}}}
        self.shapes, schemas = {}, []
        for name, body in (("state", state), ("collected", collected)):
            body.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$defs": artifact.get("$defs", {})})
            raw = canonical(body)
            ref = {"schema_id": "fixture.population-" + name, "version": "1", "sha256": hashlib.sha256(raw).hexdigest()}
            self.shapes[name] = {"kind": "artifact", "schema_ref": ref, "media_type": "application/json",
                                 "representation": "synthetic-population", "unit": "1"}
            schemas.append(PinnedSchema(SchemaIdentity(ref["schema_id"], ref["version"], ref["sha256"]), raw))
        self.schemas, self.tools, self.bindings = SchemaCatalog(schemas), [], {}
        for name in ("seed", "slice", "prepare", "evaluate_a", "evaluate_b", "assemble", "collect", "select", "vary"):
            self.add(name, {"parameters": "collected" if name in {"assemble", "collect"} else "state"})
        for count in range(1, 5):
            self.add("process_" + str(count), {"p" + str(i): "state" for i in range(count)})

    def add(self, name, inputs):
        def port(label, shape):
            return {"name": label, **{key: self.shapes[shape][key] for key in ("schema_ref", "representation", "unit")}, "required": True}
        binding = {"capability_id": "fixture.population." + name, "release": "0.1.0",
                   "image_sha256": "c" * 64, "contract_version": "1"}
        raw = {"schema_version": "1", "tool": {"schema_version": "1", "binding": binding,
               "purpose": "Compiler composition fixture only", "applicability": ["synthetic_only"],
               "inputs": [port(label, shape) for label, shape in inputs.items()], "outputs": [port("result", "state")],
               "side_effects": "pure", "checkpoint_schema": None},
               "resources": {"architectures": ["x86_64"], "operating_systems": ["windows"], "cpu_millicores": 1000,
                             "memory_mib": 128, "gpu_count": 0, "timeout_seconds": 60,
                             "max_parallel_invocations": 8, "max_batch_size": 32},
               "egress": {"mode": "deny"}, "checkpoint": {"mode": "none", "readable_schema_sha256": []},
               "reproducibility": "deterministic", "authority_ceiling": "synthetic_only",
               "examples": ["compiler test"], "anti_examples": ["scientific prediction"]}
        descriptor = ReleaseDescriptor.model_validate_json(json.dumps(raw))
        digest = hashlib.sha256(canonical({"profile": "amphora-tool-release-v1", "descriptor": descriptor.model_dump(mode="json")})).hexdigest()
        lock = {"tool": binding, "descriptor_sha256": digest, "checkpoint_schema": None,
                **{direction + "_schemas": [{"port": p["name"], "schema_ref": p["schema_ref"]} for p in raw["tool"][direction + "s"]]
                   for direction in ("input", "output")}}
        self.tools.append(ResolvedTool(descriptor, LockEntry.model_validate_json(json.dumps(lock))))
        self.bindings[name] = binding

    @property
    def resolved(self):
        return ToolCatalog(self.tools)
