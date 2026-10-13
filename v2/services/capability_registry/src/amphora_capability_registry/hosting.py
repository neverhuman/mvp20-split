"""Explicit registry configuration; secrets use environment references, startup is read-only."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from amphora_contracts_core import Identifier, SafePositiveInt, Scope, SchemaRef, WireModel
from amphora_contracts_tools import LockEntry
from .structural_profiles import StructuralGrant, StructuralPolicy
from pydantic import Field
from sqlalchemy import create_engine, text

from .access import Credentials
from .api import create_app
from .catalog.model import Principal
from .catalog.service import Registry
from .descriptors.policy import PermissionPolicy
from .descriptors.requirements import ResourceAllowance

EnvironmentName = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")]
Action = Literal["register", "activate", "drain", "revoke", "read", "deploy", "drain_deployment", "revoke_deployment", "heartbeat", "resolve"]


class ResourceProfile(WireModel):
    architecture: Literal["x86_64", "aarch64"]
    operating_system: Literal["windows", "linux"]
    cpu_millicores: SafePositiveInt
    memory_mib: SafePositiveInt
    gpu_count: Annotated[int, Field(ge=0, le=64)]
    timeout_seconds: SafePositiveInt
    max_parallel_invocations: SafePositiveInt
    max_batch_size: SafePositiveInt


class PrincipalConfig(WireModel):
    actor_id: Identifier
    scope: Scope
    token_env: EnvironmentName
    actions: Annotated[tuple[Action, ...], Field(min_length=1, max_length=10)]


class StructuralGrantConfig(WireModel):
    profile: Literal["supplied-finite-structure-v1"]
    scope: Scope
    release: LockEntry
    semantic_profile: SchemaRef
    context: Literal["supplied-finite-molecules"]

    def to_domain(self):
        return StructuralGrant(self.scope, self.release, self.semantic_profile, self.context)


class HostConfig(WireModel):
    database_url_env: EnvironmentName
    principals: Annotated[tuple[PrincipalConfig, ...], Field(min_length=1, max_length=64)]
    resources: ResourceProfile
    allowed_egress_hosts: Annotated[tuple[str, ...], Field(max_length=64)] = ()
    structural_profiles: Annotated[tuple[StructuralGrantConfig, ...], Field(max_length=64)] = ()


@dataclass(slots=True)
class Host:
    registry: Registry
    credentials: Credentials

    def app(self):
        return create_app(self.registry, self.credentials)

    def close(self):
        self.registry.engine.dispose()

    @classmethod
    def load(cls, path):
        path = Path(path)
        if path.stat().st_size > 262144:
            raise ValueError("Configuration size limit exceeded")
        config = HostConfig.model_validate_json(path.read_bytes())
        entries, identities = [], set()
        for item in config.principals:
            key = item.actor_id, item.scope.tenant_id, item.scope.project_id
            if key in identities or len(set(item.actions)) != len(item.actions):
                raise ValueError("Ambiguous principal configuration")
            identities.add(key)
            principal = Principal(item.actor_id, item.scope, frozenset(item.actions))
            entries.append((os.environ[item.token_env], principal))
        credentials = Credentials(entries)
        resources = ResourceAllowance(**config.resources.model_dump())
        permissions = PermissionPolicy(config.allowed_egress_hosts)
        structural = StructuralPolicy(tuple(grant.to_domain() for grant in config.structural_profiles))
        engine = create_engine(os.environ[config.database_url_env], pool_pre_ping=True,
                               connect_args={"options": "-c statement_timeout=5000"})
        try:
            with engine.connect() as connection:
                if connection.execute(text("SELECT current_user")).scalar_one() != "registry_service":
                    raise ValueError("Registry service role required")
                connection.execute(text("SELECT canonical_bytes,lock_entry FROM registry.releases LIMIT 0"))
                connection.execute(text("SELECT revision,status FROM registry.release_states LIMIT 0"))
                connection.execute(text("SELECT receipt FROM registry.commands LIMIT 0"))
            return cls(Registry(engine, resources, permissions, structural), credentials)
        except BaseException:
            engine.dispose()
            raise
