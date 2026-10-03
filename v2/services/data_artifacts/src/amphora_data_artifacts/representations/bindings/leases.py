"""DB-clock publication claims independent of encoding-cache computation claims."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from ...source_rights.ledger import SourceRights
from ..storage.claims import LeasePolicy
from ..storage.records import authorize
from ..validation import identifier, require
from .identity import SourceBindingIdentity
from .records import BINDING, load_job, lock_binding, published


@dataclass(frozen=True, slots=True)
class BindingLease:
    identity: SourceBindingIdentity
    token: str
    fence: int
    expires_at: datetime

    def __post_init__(self):
        require(type(self.identity) is SourceBindingIdentity, "representation_binding_required")
        identifier(self.token)
        require(type(self.fence) is int and 1 <= self.fence <= 9007199254740991, "representation_fence_bound")
        require(
            type(self.expires_at) is datetime and self.expires_at.utcoffset() is not None,
            "representation_lease_time",
        )

    def authorize(self, principal):
        require(
            self.identity.actor_id == principal.actor_id and self.identity.scope == principal.scope,
            "representation_claim_actor",
        )


@dataclass(frozen=True, slots=True)
class BindingBusy:
    binding_id: str
    expires_at: datetime


def cursor(connection, key):
    return (
        connection.execute(
            text(
                "SELECT *,expires_at>clock_timestamp() AS live "
                "FROM artifacts.encoding_binding_cursors WHERE " + BINDING
            ),
            key,
        )
        .mappings()
        .one_or_none()
    )


def fenced(connection, principal, lease):
    require(type(lease) is BindingLease, "representation_claim_required")
    lease.authorize(principal)
    key = lock_binding(connection, principal, lease.identity.binding_id)
    row = cursor(connection, key)
    require(
        row is not None and row["live"] and row["token"] == lease.token and row["fence"] == lease.fence,
        "representation_stale_claim",
    )
    return key, row


class BindingLeases:
    def __init__(self, engine, policy=None):
        policy = LeasePolicy() if policy is None else policy
        require(type(policy) is LeasePolicy, "representation_lease_policy")
        self.engine = engine
        self.policy = policy
        self.rights = SourceRights(engine)

    def claim(self, principal, binding_id):
        authorize(principal, "representation_encode")
        with self.engine.begin() as connection:
            job = load_job(connection, principal, binding_id)
            done = published(connection, principal, binding_id)
            if done is not None:
                return done
            self.rights.authorize(
                connection, principal, (job.identity.source.source.raw.artifact_id,), use="process"
            )
            key = lock_binding(connection, principal, binding_id)
            done = published(connection, principal, binding_id)
            if done is not None:
                return done
            row = cursor(connection, key)
            if row is not None and row["live"]:
                return BindingBusy(binding_id, row["expires_at"])
            fence = 1 if row is None else row["fence"] + 1
            require(fence <= 9007199254740991, "representation_fence_exhausted")
            token = uuid.uuid4().hex
            expiry = connection.execute(
                text(
                    "INSERT INTO artifacts.encoding_binding_cursors "
                    "(tenant_id,project_id,binding_id,token,fence,expires_at) VALUES "
                    "(:tenant,:project,:binding,:token,:fence,clock_timestamp()+:seconds*interval '1 second') "
                    "ON CONFLICT (tenant_id,project_id,binding_id) DO UPDATE SET token=EXCLUDED.token,"
                    "fence=EXCLUDED.fence,expires_at=EXCLUDED.expires_at RETURNING expires_at"
                ),
                key | {"token": token, "fence": fence, "seconds": self.policy.seconds},
            ).scalar_one()
            return BindingLease(job.identity, token, fence, expiry)

    def renew(self, principal, lease):
        authorize(principal, "representation_encode")
        with self.engine.begin() as connection:
            key, row = fenced(connection, principal, lease)
            require(row["stage"] != "published", "representation_binding_complete")
            expiry = connection.execute(
                text(
                    "UPDATE artifacts.encoding_binding_cursors SET "
                    "expires_at=clock_timestamp()+:seconds*interval '1 second' WHERE "
                    + BINDING
                    + " RETURNING expires_at"
                ),
                key | {"seconds": self.policy.seconds},
            ).scalar_one()
            return BindingLease(lease.identity, lease.token, lease.fence, expiry)

    def release(self, principal, lease):
        authorize(principal, "representation_encode")
        require(type(lease) is BindingLease, "representation_claim_required")
        lease.authorize(principal)
        with self.engine.begin() as connection:
            key = lock_binding(connection, principal, lease.identity.binding_id)
            row = cursor(connection, key)
            if row is None or not row["live"] or (row["token"], row["fence"]) != (lease.token, lease.fence):
                return False
            connection.execute(
                text(
                    "UPDATE artifacts.encoding_binding_cursors SET expires_at=clock_timestamp() WHERE "
                    + BINDING
                ),
                key,
            )
            return True
