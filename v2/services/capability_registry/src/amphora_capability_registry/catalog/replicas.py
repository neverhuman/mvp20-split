"""Replica lease policy owns identity, revision, capacity and observed time."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from amphora_contracts_tools import HeartbeatSnapshot

from .model import RegistryDenied


@dataclass(frozen=True, slots=True)
class ReplicaIdentity:
    deployment_id: str
    replica_id: str
    worker_id: str


@dataclass(frozen=True, slots=True)
class ReplicaLease:
    identity: ReplicaIdentity
    revision: int
    free_slots: int
    observed_at: datetime
    expires_at: datetime

    def to_wire(self, scope):
        return HeartbeatSnapshot(scope=scope, deployment_id=self.identity.deployment_id,
            replica_id=self.identity.replica_id, worker_id=self.identity.worker_id, revision=self.revision,
            free_slots=self.free_slots, observed_at=self.observed_at, expires_at=self.expires_at)

    def bindings(self):
        return {"worker": self.identity.worker_id, "revision": self.revision, "slots": self.free_slots,
                "observed": self.observed_at, "expires": self.expires_at}


class ReplicaPolicy:
    retained_limit = 64

    def observe(self, principal, report, deployment, release, previous, retained_count, now):
        if deployment["status"] != "active" or release.lifecycle.status != "active":
            raise RegistryDenied("deployment_not_active")
        if principal.actor_id not in deployment["definition"]["workers"]:
            raise RegistryDenied("replica_worker_denied")
        if report.free_slots > release.descriptor.resources.max_parallel_invocations:
            raise RegistryDenied("replica_capacity_exceeded")
        if previous is not None and previous["worker_id"] != principal.actor_id:
            raise RegistryDenied("replica_owner_conflict")
        if report.expected_revision != (0 if previous is None else previous["revision"]):
            raise RegistryDenied("revision_conflict")
        if report.expected_revision == 9007199254740991:
            raise RegistryDenied("revision_exhausted")
        if previous is None and retained_count >= self.retained_limit:
            raise RegistryDenied("replica_limit")
        identity = ReplicaIdentity(report.deployment_id, report.replica_id, principal.actor_id)
        return ReplicaLease(identity, report.expected_revision + 1, report.free_slots, now,
                            now + timedelta(seconds=report.ttl_seconds))
