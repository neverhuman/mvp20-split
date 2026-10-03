"""Persisted single-flight claims and DB-clock lease transitions; no computation."""

import uuid

from sqlalchemy import text

from ..identity import EncodingWorkIdentity
from ..validation import require
from .claims import CacheHit, LeasePolicy, WorkBusy, WorkLease
from .records import WORK, authorize, decode_result, load_profile, load_work, lock_work, result_row

MATCH = WORK + " AND actor_id=:actor AND token=:token AND fence=:fence AND expires_at>clock_timestamp()"
DEFAULT_POLICY = LeasePolicy()


class WorkLeases:
    def __init__(self, engine, policy=DEFAULT_POLICY):
        require(type(policy) is LeasePolicy, "representation_lease_policy")
        self.engine = engine
        self.policy = policy

    def claim(self, principal, ref, source):
        authorize(principal, "representation_encode")
        with self.engine.begin() as connection:
            profile = load_profile(connection, principal, ref)
            work = EncodingWorkIdentity.prepare(principal.scope, profile, source)
            key = lock_work(connection, principal, work)
            connection.execute(
                text(
                    "INSERT INTO artifacts.encoding_work "
                    "(tenant_id,project_id,work_sha256,profile_id,version,profile_sha256,input_sha256,context_sha256,actor_id) "
                    "VALUES (:tenant,:project,:work,:profile,:version,:digest,:input,:context,:actor) "
                    "ON CONFLICT (tenant_id,project_id,work_sha256) DO NOTHING"
                ),
                key
                | {
                    "profile": ref.profile_id,
                    "version": ref.version,
                    "digest": ref.sha256,
                    "input": work.input_sha256,
                    "context": work.context_sha256,
                },
            )
            load_work(connection, principal, work)
            completed = result_row(connection, principal, work)
            if completed is not None:
                return CacheHit(work, decode_result(principal, work, profile, completed))
            lease = (
                connection.execute(
                    text(
                        "SELECT *,expires_at>clock_timestamp() AS live "
                        "FROM artifacts.encoding_leases WHERE " + WORK
                    ),
                    key,
                )
                .mappings()
                .one_or_none()
            )
            if lease is not None and lease["live"]:
                return WorkBusy(work, lease["expires_at"])
            token = uuid.uuid4().hex
            fence = 1 if lease is None else lease["fence"] + 1
            require(fence <= 9007199254740991, "representation_fence_exhausted")
            expiry = connection.execute(
                text(
                    "INSERT INTO artifacts.encoding_leases "
                    "(tenant_id,project_id,work_sha256,actor_id,token,fence,expires_at) "
                    "VALUES (:tenant,:project,:work,:actor,:token,:fence,clock_timestamp()+:seconds*interval '1 second') "
                    "ON CONFLICT (tenant_id,project_id,work_sha256) DO UPDATE SET actor_id=EXCLUDED.actor_id,"
                    "token=EXCLUDED.token,fence=EXCLUDED.fence,expires_at=EXCLUDED.expires_at RETURNING expires_at"
                ),
                key | {"token": token, "fence": fence, "seconds": self.policy.seconds},
            ).scalar_one()
            return WorkLease(work, principal.actor_id, token, fence, expiry)

    def renew(self, principal, lease):
        authorize(principal, "representation_encode")
        require(type(lease) is WorkLease, "representation_claim_required")
        lease.authorize(principal)
        with self.engine.begin() as connection:
            key = lock_work(connection, principal, lease.work) | lease.identity
            require(result_row(connection, principal, lease.work) is None, "representation_work_complete")
            expiry = connection.execute(
                text(
                    "UPDATE artifacts.encoding_leases "
                    "SET expires_at=clock_timestamp()+:seconds*interval '1 second' WHERE "
                    + MATCH
                    + " RETURNING expires_at"
                ),
                key | {"seconds": self.policy.seconds},
            ).scalar_one_or_none()
            require(expiry is not None, "representation_stale_claim")
            return WorkLease(lease.work, lease.actor_id, lease.token, lease.fence, expiry)

    def release(self, principal, lease):
        authorize(principal, "representation_encode")
        require(type(lease) is WorkLease, "representation_claim_required")
        lease.authorize(principal)
        with self.engine.begin() as connection:
            key = lock_work(connection, principal, lease.work) | lease.identity
            if result_row(connection, principal, lease.work) is not None:
                return False
            changed = connection.execute(
                text("UPDATE artifacts.encoding_leases SET expires_at=clock_timestamp() WHERE " + MATCH), key
            ).rowcount
            return changed == 1
