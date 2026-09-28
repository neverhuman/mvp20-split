"""Declared installations and authenticated expiring replica observations."""

import json
from datetime import timedelta

from amphora_contracts_tools import (
    ChangeDeployment,
    DeploymentSnapshot,
    HeartbeatSnapshot,
    RegisterDeployment,
    ReplicaHeartbeat,
)
from sqlalchemy import text

from ..persistence.store import scope_bindings
from .model import Lifecycle, RegistryDenied
from .releases import read_release


def deployment_row(connection, scope, deployment_id):
    row = connection.execute(text("SELECT * FROM registry.deployments WHERE tenant_id=:tenant AND project_id=:project "
        "AND deployment_id=:deployment"), {**scope_bindings(scope), "deployment": deployment_id}).mappings().one_or_none()
    if row is None:
        raise RegistryDenied("deployment_not_found")
    return row


def deployment_wire(scope, row):
    return DeploymentSnapshot(scope=scope, deployment=RegisterDeployment.model_validate_json(json.dumps(row["definition"])),
                              revision=row["revision"], status=row["status"])


class Inventory:
    def deploy(self, connection, scope, raw, factory):
        definition = RegisterDeployment.model_validate_json(json.dumps(raw))
        record = read_release(connection, scope, definition.release.descriptor_sha256)
        record.document.verify_lock(definition.release)
        if record.lifecycle.status != "active":
            raise RegistryDenied("release_not_active")
        if len(set(definition.workers)) != len(definition.workers):
            raise RegistryDenied("duplicate_worker")
        resources = record.descriptor.resources
        if definition.architecture not in resources.architectures or definition.operating_system not in resources.operating_systems:
            raise RegistryDenied("deployment_platform_unsupported")
        values = {**scope_bindings(scope), "deployment": definition.deployment_id, "digest": record.document.digest}
        existing = connection.execute(text("SELECT * FROM registry.deployments WHERE tenant_id=:tenant AND project_id=:project "
            "AND deployment_id=:deployment"), values).mappings().one_or_none()
        if existing is not None:
            if existing["definition"] != definition.model_dump(mode="json"):
                raise RegistryDenied("immutable_deployment_conflict")
            return factory.accepted("existing", deployment=deployment_wire(scope, existing))
        count = connection.execute(text("SELECT count(*) FROM registry.deployments WHERE tenant_id=:tenant AND project_id=:project "
            "AND descriptor_sha256=:digest"), values).scalar_one()
        if count >= 64:
            raise RegistryDenied("deployment_limit")
        connection.execute(text("INSERT INTO registry.deployments (tenant_id,project_id,deployment_id,descriptor_sha256,definition,revision,status) "
            "VALUES (:tenant,:project,:deployment,:digest,CAST(:definition AS jsonb),1,'active')"),
            {**values, "definition": definition.model_dump_json()})
        return factory.accepted("deployed", deployment=deployment_wire(scope, deployment_row(connection, scope, definition.deployment_id)))

    def change(self, connection, scope, action, raw, factory):
        payload = ChangeDeployment.model_validate_json(json.dumps(raw))
        row = deployment_row(connection, scope, payload.deployment_id)
        lifecycle = Lifecycle(row["status"], row["revision"]).changed(action.removesuffix("_deployment"), payload.expected_revision)
        connection.execute(text("UPDATE registry.deployments SET status=:status,revision=:revision "
            "WHERE tenant_id=:tenant AND project_id=:project AND deployment_id=:deployment"),
            {**scope_bindings(scope), "deployment": payload.deployment_id, "status": lifecycle.status, "revision": lifecycle.revision})
        return factory.accepted(lifecycle.status, deployment=deployment_wire(scope, deployment_row(connection, scope, payload.deployment_id)))

    def heartbeat(self, connection, principal, raw, factory):
        payload = ReplicaHeartbeat.model_validate_json(json.dumps(raw))
        scope = principal.scope
        row = deployment_row(connection, scope, payload.deployment_id)
        release = read_release(connection, scope, row["descriptor_sha256"])
        if row["status"] != "active" or release.lifecycle.status != "active":
            raise RegistryDenied("deployment_not_active")
        if principal.actor_id not in row["definition"]["workers"]:
            raise RegistryDenied("replica_worker_denied")
        if payload.free_slots > release.descriptor.resources.max_parallel_invocations:
            raise RegistryDenied("replica_capacity_exceeded")
        values = {**scope_bindings(scope), "deployment": payload.deployment_id, "replica": payload.replica_id}
        previous = connection.execute(text("SELECT * FROM registry.replicas WHERE tenant_id=:tenant AND project_id=:project "
            "AND deployment_id=:deployment AND replica_id=:replica"), values).mappings().one_or_none()
        if previous is not None and previous["worker_id"] != principal.actor_id:
            raise RegistryDenied("replica_owner_conflict")
        if payload.expected_revision != (0 if previous is None else previous["revision"]):
            raise RegistryDenied("revision_conflict")
        if payload.expected_revision == 9007199254740991:
            raise RegistryDenied("revision_exhausted")
        if previous is None:
            count = connection.execute(text("SELECT count(*) FROM registry.replicas WHERE tenant_id=:tenant AND project_id=:project "
                "AND deployment_id=:deployment"), values).scalar_one()
            if count >= 64:
                raise RegistryDenied("replica_limit")
        now = connection.execute(text("SELECT clock_timestamp()")).scalar_one()
        snapshot = HeartbeatSnapshot(scope=scope, deployment_id=payload.deployment_id, replica_id=payload.replica_id,
            worker_id=principal.actor_id, revision=payload.expected_revision+1, free_slots=payload.free_slots,
            observed_at=now, expires_at=now+timedelta(seconds=payload.ttl_seconds))
        connection.execute(text("INSERT INTO registry.replicas (tenant_id,project_id,deployment_id,replica_id,worker_id,revision,"
            "free_slots,observed_at,expires_at) VALUES (:tenant,:project,:deployment,:replica,:worker,:revision,:slots,:observed,:expires) "
            "ON CONFLICT (tenant_id,project_id,deployment_id,replica_id) DO UPDATE SET revision=EXCLUDED.revision,"
            "free_slots=EXCLUDED.free_slots,observed_at=EXCLUDED.observed_at,expires_at=EXCLUDED.expires_at"),
            {**values, "worker": snapshot.worker_id, "revision": snapshot.revision, "slots": snapshot.free_slots,
             "observed": snapshot.observed_at, "expires": snapshot.expires_at})
        return factory.accepted("observed", heartbeat=snapshot)
