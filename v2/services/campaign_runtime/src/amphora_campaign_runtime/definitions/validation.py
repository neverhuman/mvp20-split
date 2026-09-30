"""Pure reviewed-universe compilation; no scientific or execution grant."""

import base64
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Finding, SchemaRef, Scope
from amphora_contracts_graph_runtime import DraftValidation
from amphora_contracts_tools import LockEntry, ReleaseDescriptor

from ..compiler import (
    CompilationError,
    PinnedSchema,
    ResolvedTool,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
)
from ..coordinator.plans import ReviewedPlan
from .revisions import DraftVersion


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    draft: DraftVersion
    universe_sha256: str
    entry: ReviewedPlan | None
    findings: tuple[Finding, ...]

    def to_wire(self, validation_id):
        return DraftValidation(scope=self.draft.content.definition.scope, validation_id=validation_id,
            draft_id=self.draft.draft_id, revision=self.draft.revision, content_sha256=self.draft.content.sha256,
            universe_sha256=self.universe_sha256, structurally_valid=self.entry is not None,
            plan_sha256=None if self.entry is None else self.entry.plan.sha256, findings=self.findings,
            pending_checks=("current_eligibility", "activation", "scientific_applicability"))


@dataclass(frozen=True, slots=True)
class ValidationUniverse:
    scope: Scope
    releases: tuple[ResolvedTool, ...]
    schemas: tuple[PinnedSchema, ...]

    def __post_init__(self):
        object.__setattr__(self, "releases", tuple(self.releases))
        object.__setattr__(self, "schemas", tuple(self.schemas))
        if len(self.releases) > 64 or len(self.schemas) > 256:
            raise ValueError("authoring_universe_bound")
        ToolCatalog(self.releases)
        SchemaCatalog(self.schemas)

    @property
    def sha256(self):
        document = {"profile": "amphora-authoring-universe-v1", "compiler": "amphora-deterministic-compiler-v3",
            "scope": self.scope.model_dump(mode="json"),
            "tools": sorted((tool.lock.model_dump(mode="json") for tool in self.releases), key=lambda item: canonical(item)),
            "schemas": sorted((schema.identity.record() for schema in self.schemas), key=lambda item: canonical(item))}
        return hashlib.sha256(canonical(document)).hexdigest()

    def validate(self, draft):
        if draft.content.definition.scope != self.scope:
            raise ValueError("draft_universe_scope_mismatch")
        try:
            entry = ReviewedPlan.compile(draft.content.definition, ToolCatalog(self.releases), SchemaCatalog(self.schemas))
        except CompilationError as error:
            return ValidationOutcome(draft, self.sha256, None, error.findings)
        return ValidationOutcome(draft, self.sha256, entry, ())

    def record(self):
        return {"profile": "amphora-authoring-universe-v1", "scope": self.scope.model_dump(mode="json"),
            "tools": [{"descriptor": tool.descriptor.model_dump(mode="json"), "lock": tool.lock.model_dump(mode="json")} for tool in self.releases],
            "schemas": [{"identity": schema.identity.record(), "bytes": base64.b64encode(schema.source_bytes).decode()} for schema in self.schemas]}

    @classmethod
    def restore(cls, record, expected_sha256):
        if set(record) != {"profile", "scope", "tools", "schemas"} or record["profile"] != "amphora-authoring-universe-v1":
            raise ValueError("unknown_authoring_universe_profile")
        if not isinstance(record["tools"], list) or not isinstance(record["schemas"], list) or len(record["tools"]) > 64 or len(record["schemas"]) > 256:
            raise ValueError("authoring_universe_bound")
        for schema in record["schemas"]:
            if set(schema) != {"identity", "bytes"} or not isinstance(schema["bytes"], str) or len(schema["bytes"]) > 87384:
                raise ValueError("invalid_retained_schema")
        if any(set(tool) != {"descriptor", "lock"} for tool in record["tools"]):
            raise ValueError("invalid_retained_tool")
        result = cls(Scope.model_validate_json(json.dumps(record["scope"])),
            tuple(ResolvedTool(ReleaseDescriptor.model_validate_json(json.dumps(tool["descriptor"])),
                LockEntry.model_validate_json(json.dumps(tool["lock"]))) for tool in record["tools"]),
            tuple(PinnedSchema(SchemaIdentity.from_wire(SchemaRef.model_validate_json(json.dumps(schema["identity"]))),
                base64.b64decode(schema["bytes"], validate=True)) for schema in record["schemas"]))
        if result.sha256 != expected_sha256:
            raise ValueError("authoring_universe_digest_mismatch")
        return result
