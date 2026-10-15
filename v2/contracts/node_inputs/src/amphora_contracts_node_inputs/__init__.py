"""Original retained input observations, never execution or acceptance authority."""
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, Scope, WireModel
from amphora_contracts_runtime import PreparedInvocation
from pydantic import Field, model_validator

Count = Annotated[int, Field(ge=0, le=10000)]


class ScopeInputSummary(WireModel):
    port: Identifier
    kind: Literal["artifact", "boolean", "integer", "number", "string", "collection"]
    item_count: Count
    missing_count: Count
    artifact: ArtifactRef | None = None

    @model_validator(mode="after")
    def consistent_summary(self):
        if self.missing_count > self.item_count:
            raise ValueError("missing_count_exceeds_items")
        if (self.artifact is not None) != (self.kind == "artifact"):
            raise ValueError("artifact_summary_mismatch")
        if self.kind != "collection" and (self.item_count != 1 or self.missing_count != 0):
            raise ValueError("singleton_summary_mismatch")
        return self


class NodeInputObservation(WireModel):
    schema_version: Literal["1"]
    profile: Literal["runtime-node-inputs-v1"]
    scope: Scope
    run_id: Identifier
    activation_id: Digest
    scope_key: Digest
    observed_run_revision: Annotated[int, Field(ge=0, le=9007199254740991)]
    scope_inputs: Annotated[tuple[ScopeInputSummary, ...], Field(max_length=64)]
    invocation: PreparedInvocation | None

    @model_validator(mode="after")
    def consistent_identity(self):
        if len({item.port for item in self.scope_inputs}) != len(self.scope_inputs):
            raise ValueError("duplicate_scope_input")
        refs = [item.artifact for item in self.scope_inputs if item.artifact is not None]
        if self.invocation is not None:
            if self.invocation.activation_id != self.activation_id:
                raise ValueError("invocation_activation_mismatch")
            refs.extend(binding.artifact for binding in self.invocation.inputs)
            if self.invocation.checkpoint is not None:
                refs.append(self.invocation.checkpoint)
        if any(ref.scope != self.scope for ref in refs):
            raise ValueError("cross_scope_input")
        if len(self.model_dump_json().encode("utf-8")) > 262144:
            raise ValueError("input_observation_too_large")
        return self


__all__ = ["NodeInputObservation", "ScopeInputSummary"]
