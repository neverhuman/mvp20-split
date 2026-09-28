"""Additive registry wire roots; legacy execution descriptor bytes stay unchanged."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Finding, Identifier, SchemaRef, Scope, WireModel
from pydantic import Field

from .models import ToolBinding, ToolDescriptor


class ResourceBounds(WireModel):
    architectures: Annotated[tuple[Literal["x86_64", "aarch64"], ...], Field(min_length=1, max_length=2)]
    operating_systems: Annotated[tuple[Literal["linux", "windows"], ...], Field(min_length=1, max_length=2)]
    cpu_millicores: Annotated[int, Field(ge=1, le=1048576)]
    memory_mib: Annotated[int, Field(ge=1, le=1048576)]
    gpu_count: Annotated[int, Field(ge=0, le=64)]
    timeout_seconds: Annotated[int, Field(ge=1, le=86400)]
    max_parallel_invocations: Annotated[int, Field(ge=1, le=1024)]
    max_batch_size: Annotated[int, Field(ge=1, le=65536)]


class DeniedEgress(WireModel):
    mode: Literal["deny"]


class AllowedEgress(WireModel):
    mode: Literal["allowlist"]
    hosts: Annotated[tuple[Annotated[str, Field(min_length=1, max_length=253,
        pattern=r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")], ...], Field(min_length=1, max_length=64)]


class CheckpointCompatibility(WireModel):
    mode: Literal["none", "opaque_artifact"]
    readable_schema_sha256: Annotated[tuple[Digest, ...], Field(max_length=64)]


class ReleaseDescriptor(WireModel):
    schema_version: Literal["1"]
    tool: ToolDescriptor
    resources: ResourceBounds
    egress: Annotated[DeniedEgress | AllowedEgress, Field(discriminator="mode")]
    checkpoint: CheckpointCompatibility
    reproducibility: Literal["deterministic", "seeded", "nondeterministic"]
    authority_ceiling: Literal["synthetic_only", "evidence_proposal"]
    examples: Annotated[tuple[Annotated[str, Field(min_length=1, max_length=2048)], ...], Field(min_length=1, max_length=16)]
    anti_examples: Annotated[tuple[Annotated[str, Field(min_length=1, max_length=2048)], ...], Field(min_length=1, max_length=16)]


class PortSchemaLock(WireModel):
    port: Identifier
    schema_ref: SchemaRef


class LockEntry(WireModel):
    schema_version: Literal["1"] = "1"
    tool: ToolBinding
    descriptor_sha256: Digest
    input_schemas: Annotated[tuple[PortSchemaLock, ...], Field(max_length=64)]
    output_schemas: Annotated[tuple[PortSchemaLock, ...], Field(max_length=64)]
    checkpoint_schema: SchemaRef | None


class StructuralAssessment(WireModel):
    status: Literal["valid", "invalid"]
    findings: Annotated[tuple[Finding, ...], Field(max_length=128)]


class ScientificEligibility(WireModel):
    status: Literal["eligible", "ineligible", "unreviewed"]
    reason_codes: Annotated[tuple[Identifier, ...], Field(max_length=64)]


class CapacityAssessment(WireModel):
    status: Literal["available", "unavailable", "unknown"]
    reason_codes: Annotated[tuple[Identifier, ...], Field(max_length=64)]


class EligibilityResult(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    release: LockEntry
    policy_sha256: Digest
    structural: StructuralAssessment
    scientific: ScientificEligibility
    capacity: CapacityAssessment


class RegisterRelease(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    descriptor: ReleaseDescriptor
    expected_lock: LockEntry


class ReleaseRegistrationReceipt(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    release: LockEntry
    disposition: Literal["registered", "existing", "conflict"]
    reason_code: Identifier
