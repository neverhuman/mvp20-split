"""Registry transport; registration, lifecycle and capacity are separate authorities."""

import json
from datetime import datetime
from typing import Annotated, Literal

from amphora_contracts_commands import CanonicalCommand, CommandEncodingError
from amphora_contracts_core import Digest, Identifier, SafePositiveInt, Scope, WireModel
from pydantic import AfterValidator, Field

from .models import Port
from .releases import EligibilityDecision, LockEntry, RegisterRelease, ReleaseDescriptor, aware_timestamp

Revision = Annotated[int, Field(ge=0, le=9007199254740991)]
Timestamp = Annotated[datetime, AfterValidator(aware_timestamp)]


class ChangeRelease(WireModel):
    release: LockEntry
    expected_revision: SafePositiveInt


class RegisterDeployment(WireModel):
    deployment_id: Identifier
    release: LockEntry
    architecture: Literal["x86_64", "aarch64"]
    operating_system: Literal["linux", "windows"]
    workers: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=64)]


class ChangeDeployment(WireModel):
    deployment_id: Identifier
    expected_revision: SafePositiveInt


class ReplicaHeartbeat(WireModel):
    deployment_id: Identifier
    replica_id: Identifier
    expected_revision: Revision
    free_slots: Annotated[int, Field(ge=0, le=1024)]
    ttl_seconds: Annotated[int, Field(ge=1, le=60)]


class ResolveRelease(WireModel):
    release: LockEntry
    context: Identifier
    inputs: Annotated[tuple[Port, ...], Field(max_length=64)]
    outputs: Annotated[tuple[Port, ...], Field(min_length=1, max_length=64)]


class ReleaseSnapshot(WireModel):
    scope: Scope
    descriptor: ReleaseDescriptor
    lock: LockEntry
    revision: SafePositiveInt
    status: Literal["registered", "active", "draining", "revoked"]


class DeploymentSnapshot(WireModel):
    scope: Scope
    deployment: RegisterDeployment
    revision: SafePositiveInt
    status: Literal["active", "draining", "revoked"]


class ReleasePage(WireModel):
    schema_version: Literal["1"] = "1"
    items: Annotated[tuple[ReleaseSnapshot, ...], Field(max_length=100)]
    next_after: Digest | None


class HeartbeatSnapshot(WireModel):
    scope: Scope
    deployment_id: Identifier
    replica_id: Identifier
    worker_id: Identifier
    revision: SafePositiveInt
    free_slots: Annotated[int, Field(ge=0, le=1024)]
    observed_at: Timestamp
    expires_at: Timestamp


class RegistryReceipt(WireModel):
    schema_version: Literal["1"] = "1"
    operation_id: Identifier
    status: Literal["accepted", "rejected"]
    reason_code: Identifier
    release: ReleaseSnapshot | None
    deployment: DeploymentSnapshot | None
    heartbeat: HeartbeatSnapshot | None
    decision: EligibilityDecision | None


OPERATIONS = {
    "registry.register": RegisterRelease,
    "registry.activate": ChangeRelease,
    "registry.drain": ChangeRelease,
    "registry.revoke": ChangeRelease,
    "registry.deploy": RegisterDeployment,
    "registry.drain_deployment": ChangeDeployment,
    "registry.revoke_deployment": ChangeDeployment,
    "registry.heartbeat": ReplicaHeartbeat,
    "registry.resolve": ResolveRelease,
}


def parse_registry_command(family, raw):
    if family not in OPERATIONS:
        raise CommandEncodingError("unknown_family")
    command = CanonicalCommand.for_family(raw, family, OPERATIONS[family])
    if family == "registry.register":
        scope = json.loads(command.canonical_bytes)["payload"]["scope"]
        if scope != command.identity.scope.model_dump():
            raise CommandEncodingError("scope_mismatch")
    return command
