"""Atomic own-request reservation with journal intent; never dispatches a provider."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from ..budget import BudgetPolicy, ReservationDemand
from ..checkpoint_budget import CheckpointAllowance
from ..checkpoint_budget import journal as checkpoint_budget
from ..curation_budget import CurationAllowance
from ..curation_budget import journal as curation_budget
from ..context import AttemptBinding
from ..context.policy import require
from . import family_state
from .execution_state import require_execution_open
from .journal import KEY, PlanningJournal


@dataclass(frozen=True)
class BudgetReservation:
    demand: ReservationDemand
    registered_at: datetime


class BudgetLedger:
    def __init__(self, engine):
        self.engine = engine
        self.journal = PlanningJournal(engine)

    @staticmethod
    def _policy(connection, key):
        row = connection.execute(text("SELECT * FROM planning.budget_policies WHERE " + KEY), key).mappings().first()
        if row is None:
            return None
        policy = BudgetPolicy.from_bytes(bytes(row["canonical_bytes"]))
        require(policy.sha256 == row["policy_sha256"], "stored_budget_policy_corrupt")
        return policy

    @staticmethod
    def _reservation(connection, key, binding, policy):
        row = connection.execute(text("SELECT * FROM planning.reservations WHERE " + KEY +
            " AND ordinal=:ordinal"), key).mappings().first()
        if row is None:
            return None
        require(policy is not None, "stored_budget_policy_missing")
        demand = policy.demand(binding)
        require((row["policy_sha256"], row["input_tokens"], row["output_tokens"], row["accounting_units"]) ==
                (demand.policy_sha256, demand.input_tokens, demand.output_tokens, demand.accounting_units),
                "stored_reservation_corrupt")
        return BudgetReservation(demand, row["registered_at"])

    def reserve(self, principal, binding, reviewed_policy):
        reference = binding.reference()
        principal.require("record_attempts", reference.engagement.scope)
        reviewed_policy = BudgetPolicy.from_bytes(reviewed_policy.canonical)
        demand = reviewed_policy.demand(binding)
        if CheckpointAllowance.applies(binding.request):
            CheckpointAllowance.validate_policy(reviewed_policy)
        if CurationAllowance.applies(binding.request):
            CurationAllowance.validate_policy(reviewed_policy)
        key = {**self.journal._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.begin() as connection:
            live_group = checkpoint_budget.lock(connection, key, binding.request)
            curation_group = curation_budget.lock(connection, key, binding.request)
            membership = family_state.lock_request(connection, key)
            snapshot = self.journal._request(connection, key, principal)
            require(snapshot is not None, "request_unknown")
            require(snapshot.sha256 == reference.request_sha256, "request_conflict")
            stored_policy = self._policy(connection, key)
            if stored_policy is not None:
                require(stored_policy.canonical == reviewed_policy.canonical, "budget_policy_conflict")
            existing = self._reservation(connection, key, binding, stored_policy)
            if existing is not None:
                return existing
            if live_group:
                checkpoint_budget.check(connection, key, demand)
            if curation_group:
                curation_budget.check(connection, key, demand)
            require_execution_open(connection, key)
            family_state.require_budget(connection, key, membership, self.journal, principal, reviewed_policy, demand)
            # Never retroactively authorize a journal intent created outside budget admission.
            unbudgeted = connection.execute(text("SELECT count(*) FROM planning.attempts a WHERE "
                "a.tenant_id=:tenant AND a.project_id=:project AND a.engagement_id=:engagement AND NOT EXISTS "
                "(SELECT 1 FROM planning.reservations r WHERE r.tenant_id=a.tenant_id AND r.project_id=a.project_id "
                "AND r.engagement_id=a.engagement_id AND r.ordinal=a.ordinal)"), key).scalar_one()
            require(unbudgeted == 0, "unbudgeted_attempt_history")
            if stored_policy is None:
                connection.execute(text("INSERT INTO planning.budget_policies "
                    "(tenant_id,project_id,engagement_id,request_sha256,policy_sha256,canonical_bytes) "
                    "VALUES (:tenant,:project,:engagement,:request,:policy,:content)"),
                    {**key, "request": snapshot.sha256, "policy": reviewed_policy.sha256,
                     "content": reviewed_policy.canonical})
            latest = connection.execute(text("SELECT COALESCE(MAX(ordinal),0) FROM planning.attempts WHERE " + KEY),
                                         key).scalar_one()
            require(reference.ordinal == latest + 1, "attempt_sequence")
            if latest:
                previous = self.journal._attempt(connection, {**key, "ordinal": latest}, snapshot)
                require(previous.observation is not None, "attempt_pending")
                settled = connection.execute(text("SELECT 1 FROM planning.settlements WHERE " + KEY +
                    " AND ordinal=:ordinal"), {**key, "ordinal": latest}).first()
                require(settled is not None, "attempt_unsettled")
            held = connection.execute(text("SELECT "
                "COALESCE(SUM(GREATEST(s.input_tokens,r.input_tokens,l.input_tokens)+"
                "GREATEST(s.output_tokens,r.output_tokens,l.output_tokens)),0) AS tokens, "
                "COALESCE(SUM(GREATEST(s.accounting_units,r.accounting_units,l.accounting_units)),0) AS units, "
                "COALESCE(bool_or(s.overage OR l.overage),false) AS overage "
                "FROM planning.reservations r LEFT JOIN planning.settlements s "
                "USING(tenant_id,project_id,engagement_id,ordinal) LEFT JOIN planning.late_observations l "
                "USING(tenant_id,project_id,engagement_id,ordinal) WHERE " + KEY),
                key).mappings().one()
            require(not held["overage"], "provider_usage_overage")
            limits = snapshot.document().context.limits
            require(int(held["tokens"]) + demand.tokens <= limits.total_tokens, "token_budget_exhausted")
            require(int(held["units"]) + demand.accounting_units <= limits.total_accounting_units,
                    "accounting_budget_exhausted")
            connection.execute(text("INSERT INTO planning.attempts "
                "(tenant_id,project_id,engagement_id,ordinal,request_sha256) "
                "VALUES (:tenant,:project,:engagement,:ordinal,:request)"), {**key, "request": snapshot.sha256})
            connection.execute(text("INSERT INTO planning.reservations "
                "(tenant_id,project_id,engagement_id,ordinal,policy_sha256,input_tokens,output_tokens,accounting_units) "
                "VALUES (:tenant,:project,:engagement,:ordinal,:policy,:input,:output,:units)"),
                {**key, "policy": demand.policy_sha256, "input": demand.input_tokens,
                 "output": demand.output_tokens, "units": demand.accounting_units})
            return self._reservation(connection, key, binding, reviewed_policy)

    def read(self, principal, reference):
        principal.require("read_attempts", reference.engagement.scope)
        key = {**self.journal._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.connect() as connection:
            snapshot = self.journal._request(connection, key, principal)
            if snapshot is None:
                return None
            require(snapshot.sha256 == reference.request_sha256, "request_conflict")
            policy = self._policy(connection, key)
            return self._reservation(connection, key, AttemptBinding(snapshot, reference.ordinal), policy)
