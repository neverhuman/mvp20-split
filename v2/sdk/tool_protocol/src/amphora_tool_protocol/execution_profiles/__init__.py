"""Owner-local exact structural execution grant; no chemistry or peer implementation."""
from dataclasses import dataclass
from importlib.resources import files
import hashlib
import json
from amphora_contracts_core import Scope, SchemaRef
from amphora_contracts_tools import LockEntry

PROFILE = "supplied-finite-structure-v1"
CONTEXT = "supplied-finite-molecules"

@dataclass(frozen=True, slots=True)
class StructuralExecutionProfile:
    scope: Scope
    release: LockEntry
    semantic_profile: SchemaRef
    context: str = CONTEXT

    def __post_init__(self):
        pins = json.loads(files(__package__).joinpath("reviewed.json").read_bytes())
        binding = self.release.tool
        if (self.context != CONTEXT or self.semantic_profile.model_dump() != pins["semantic_profile"]
                or binding.capability_id != "chemistry.chemical-structure" or binding.release != "0.1.0"
                or binding.contract_version != "1" or self.release.checkpoint_schema is not None):
            raise ValueError("structural_execution_profile_invalid")
        for ports, key, name in ((self.release.input_schemas, "input", "structure"),
                                  (self.release.output_schemas, "output", "result")):
            if len(ports) != 1 or ports[0].port != name or ports[0].schema_ref.model_dump() != pins[key]:
                raise ValueError("structural_execution_schema_mismatch")

    @classmethod
    def from_record(cls, record):
        if (not isinstance(record, dict) or set(record) != {"profile", "scope", "release", "semantic_profile", "context"}
                or record["profile"] != PROFILE):
            raise ValueError("structural_execution_configuration_invalid")
        return cls(Scope.model_validate_json(json.dumps(record["scope"])),
                   LockEntry.model_validate_json(json.dumps(record["release"])),
                   SchemaRef.model_validate_json(json.dumps(record["semantic_profile"])), record["context"])

    def record(self):
        return {"profile": PROFILE, "scope": self.scope.model_dump(mode="json"),
                "release": self.release.model_dump(mode="json"),
                "semantic_profile": self.semantic_profile.model_dump(mode="json"), "context": self.context}

    def require_scope(self, scope):
        if scope != self.scope:
            raise ValueError("structural_execution_scope_mismatch")

    def require_descriptor(self, descriptor, lock=None):
        document = {"profile": "amphora-tool-release-v1", "descriptor": descriptor.model_dump(mode="json")}
        digest = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"),
                                           ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        tool = descriptor.tool
        if (digest != self.release.descriptor_sha256 or tool.binding != self.release.tool
                or lock is not None and lock != self.release
                or descriptor.authority_ceiling != "evidence_proposal" or tool.side_effects != "pure"
                or descriptor.egress.mode != "deny" or descriptor.checkpoint.mode != "none"
                or tool.checkpoint_schema is not None or self.context not in tool.applicability
                or len(tool.inputs) != 1 or len(tool.outputs) != 1
                or not all(p.required for p in (*tool.inputs, *tool.outputs))):
            raise ValueError("structural_execution_descriptor_mismatch")
        for ports, pins in ((tool.inputs, self.release.input_schemas), (tool.outputs, self.release.output_schemas)):
            if tuple((p.name, p.schema_ref) for p in ports) != tuple((p.port, p.schema_ref) for p in pins):
                raise ValueError("structural_execution_descriptor_mismatch")
