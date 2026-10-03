"""Immutable scoped profile registration and digest-qualified reconstruction."""

from sqlalchemy import text

from ...persistence.evidence_records import SCOPE, _lock
from ..mapping import profile_reference, profile_to_wire
from ..validation import require
from .records import authorize, canonical, load_profile


class ProfileRegistry:
    def __init__(self, engine):
        self.engine = engine

    def register(self, principal, profile):
        authorize(principal, "representation_manage")
        ref = profile_reference(principal.scope, profile)
        body = canonical(profile_to_wire(profile))
        key = principal.bindings | {"profile": ref.profile_id, "version": ref.version}
        with self.engine.begin() as connection:
            _lock(connection, principal.scope, [("encoding-profile", ref.profile_id, ref.version)])
            existing = connection.execute(
                text(
                    "SELECT canonical_bytes FROM artifacts.encoding_profiles WHERE "
                    + SCOPE
                    + " AND profile_id=:profile AND version=:version"
                ),
                key,
            ).scalar_one_or_none()
            if existing is not None:
                require(bytes(existing) == body, "representation_profile_conflict")
                return ref
            connection.execute(
                text(
                    "INSERT INTO artifacts.encoding_profiles "
                    "(tenant_id,project_id,profile_id,version,profile_sha256,actor_id,canonical_bytes) "
                    "VALUES (:tenant,:project,:profile,:version,:digest,:actor,:body)"
                ),
                key | {"digest": ref.sha256, "body": body},
            )
        return ref

    def read(self, principal, ref):
        authorize(principal, "representation_read")
        with self.engine.begin() as connection:
            return load_profile(connection, principal, ref)
