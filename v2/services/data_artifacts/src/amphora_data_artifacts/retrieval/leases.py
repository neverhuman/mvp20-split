"""DB-clock attempt claims; immutable namespaces isolate stale builders."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from ..representations.storage.claims import LeasePolicy
from ..representations.storage.records import authorize
from ..source_rights.ledger import SourceRights
from .identity import BuildAttempt
from .intents import authorize_plan
from .lifecycle import GenerationPhase
from .mapping import status_to_wire
from .records import GENERATION, cursor, event, key_for, load_plan, lock_corpus, transition
from .validation import require


@dataclass(frozen=True, slots=True)
class GenerationLease:
    attempt: BuildAttempt
    expires_at: datetime

    def __post_init__(self):
        require(type(self.attempt) is BuildAttempt, "retrieval_attempt_required")
        require(type(self.expires_at) is datetime and self.expires_at.utcoffset() is not None, "retrieval_lease_time")


@dataclass(frozen=True, slots=True)
class GenerationBusy:
    expires_at: datetime


def fenced(connection, principal, lease):
    require(type(lease) is GenerationLease, "retrieval_claim_required")
    ref = lease.attempt.generation
    require(ref.scope == principal.scope, "retrieval_claim_scope")
    lock_corpus(connection, principal, ref.corpus_id)
    plan = load_plan(connection, principal, ref.corpus_id, ref.generation_id)
    require(plan is not None and plan.reference == ref, "retrieval_generation_conflict")
    key = key_for(principal, ref.corpus_id, ref.generation_id)
    row = cursor(connection, key)
    require(row["live"] and row["token"] == lease.attempt.token and row["fence"] == lease.attempt.fence,
        "retrieval_stale_claim")
    require(row["phase"] in {"building", "verified"}, "retrieval_generation_terminal")
    return plan, key, row


class GenerationLeases:
    def __init__(self, engine, policy=None):
        self.engine = engine
        self.policy = LeasePolicy() if policy is None else policy
        require(type(self.policy) is LeasePolicy, "retrieval_lease_policy")

    def claim(self, principal, corpus_id, generation_id):
        authorize(principal, "representation_manage")
        key = key_for(principal, corpus_id, generation_id)
        with self.engine.begin() as connection:
            SourceRights.lock(connection, principal)
            lock_corpus(connection, principal, corpus_id)
            plan = load_plan(connection, principal, corpus_id, generation_id)
            require(plan is not None, "retrieval_generation_missing")
            row = cursor(connection, key)
            phase = GenerationPhase(row["phase"])
            if phase in {GenerationPhase.PUBLISHED, GenerationPhase.FAILED, GenerationPhase.ABANDONED}:
                return status_to_wire(plan, phase)
            if phase is GenerationPhase.VERIFIED and not row["live"]:
                transition(connection, key, row, GenerationPhase.FAILED, "verification_lease_expired")
                return status_to_wire(plan, GenerationPhase.FAILED)
            authorize_plan(connection, principal, plan)
            if row["live"]:
                return GenerationBusy(row["expires_at"])
            if phase is GenerationPhase.PREPARED:
                phase.require_successor(GenerationPhase.BUILDING)
            fence, sequence = row["fence"] + 1, row["sequence"] + 1
            attempt = BuildAttempt(plan.reference, uuid.uuid4().hex, fence)
            connection.execute(text("INSERT INTO artifacts.index_build_attempts "
                "(tenant_id,project_id,corpus_id,generation_id,token,fence,namespace) VALUES "
                "(:tenant,:project,:corpus,:generation,:token,:fence,:namespace)"),
                key | {"token": attempt.token, "fence": fence, "namespace": attempt.namespace})
            event(connection, key, GenerationPhase.BUILDING, sequence, "build_claimed", attempt.token, fence)
            expires = connection.execute(text("UPDATE artifacts.index_generation_cursors SET "
                "phase='building',sequence=:sequence,token=:token,fence=:fence,"
                "expires_at=clock_timestamp()+:seconds*interval '1 second' WHERE " + GENERATION + " RETURNING expires_at"),
                key | {"sequence": sequence, "token": attempt.token, "fence": fence, "seconds": self.policy.seconds}).scalar_one()
            return GenerationLease(attempt, expires)

    def renew(self, principal, lease):
        authorize(principal, "representation_manage")
        with self.engine.begin() as connection:
            SourceRights.lock(connection, principal)
            plan, key, _ = fenced(connection, principal, lease)
            authorize_plan(connection, principal, plan)
            expires = connection.execute(text("UPDATE artifacts.index_generation_cursors SET "
                "expires_at=clock_timestamp()+:seconds*interval '1 second' WHERE " + GENERATION
                + " AND expires_at>clock_timestamp() RETURNING expires_at"),
                key | {"seconds": self.policy.seconds}).scalar_one_or_none()
            require(expires is not None, "retrieval_stale_claim")
            return GenerationLease(lease.attempt, expires)

    def finish(self, principal, lease, phase, reason):
        authorize(principal, "representation_manage")
        require(type(phase) is GenerationPhase and phase in {GenerationPhase.FAILED, GenerationPhase.ABANDONED}, "retrieval_terminal_required")
        with self.engine.begin() as connection:
            SourceRights.lock(connection, principal)
            plan, key, row = fenced(connection, principal, lease)
            transition(connection, key, row, phase, reason)
            return status_to_wire(plan, phase)

    def abandon_prepared(self, principal, corpus_id, generation_id):
        authorize(principal, "representation_manage")
        key = key_for(principal, corpus_id, generation_id)
        with self.engine.begin() as connection:
            SourceRights.lock(connection, principal)
            lock_corpus(connection, principal, corpus_id)
            plan = load_plan(connection, principal, corpus_id, generation_id)
            require(plan is not None, "retrieval_generation_missing")
            row = cursor(connection, key)
            require(row["phase"] == "prepared", "retrieval_not_prepared")
            transition(connection, key, row, GenerationPhase.ABANDONED, "owner_abandoned")
            return status_to_wire(plan, GenerationPhase.ABANDONED)
