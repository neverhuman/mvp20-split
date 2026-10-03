"""Immutable computed output and exact winning-claim replay; no Artifact publication."""

from sqlalchemy import text

from ..mapping import vector_to_wire
from ..payloads import EncodedRepresentation
from ..validation import canonical_record, require
from .claims import WorkLease
from .leases import MATCH
from .records import authorize, decode_result, load_work, lock_work, result_row


class EncodingResults:
    def __init__(self, engine):
        self.engine = engine

    def complete(self, principal, lease, result):
        authorize(principal, "representation_encode")
        require(type(lease) is WorkLease, "representation_claim_required")
        lease.authorize(principal)
        require(type(result) is EncodedRepresentation, "representation_encoded_required")
        work = lease.work
        require(
            (result.profile.reference, result.input_sha256, result.context_sha256)
            == (work.profile, work.input_sha256, work.context_sha256),
            "representation_work_conflict",
        )
        body = canonical_record(vector_to_wire(principal.scope, result))
        with self.engine.begin() as connection:
            key = lock_work(connection, principal, work) | lease.identity
            profile = load_work(connection, principal, work)
            existing = result_row(connection, principal, work)
            if existing is not None:
                require(
                    all(
                        existing[name] == value
                        for name, value in {
                            "actor_id": lease.actor_id,
                            "token": lease.token,
                            "fence": lease.fence,
                        }.items()
                    ),
                    "representation_stale_claim",
                )
                require(bytes(existing["canonical_bytes"]) == body, "representation_result_conflict")
                return decode_result(principal, work, profile, existing)
            inserted = connection.execute(
                text(
                    "INSERT INTO artifacts.encoding_results "
                    "(tenant_id,project_id,work_sha256,actor_id,token,fence,canonical_bytes) "
                    "SELECT tenant_id,project_id,work_sha256,actor_id,token,fence,:body "
                    "FROM artifacts.encoding_leases WHERE " + MATCH
                ),
                key | {"body": body},
            ).rowcount
            require(inserted == 1, "representation_stale_claim")
        return result

    def read(self, principal, work):
        authorize(principal, "representation_encode")
        with self.engine.begin() as connection:
            profile = load_work(connection, principal, work)
            existing = result_row(connection, principal, work)
            return None if existing is None else decode_result(principal, work, profile, existing)
