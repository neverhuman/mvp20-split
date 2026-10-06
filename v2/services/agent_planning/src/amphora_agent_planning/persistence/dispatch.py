"""Durable issuance fences observation acceptance, not remote physical cancellation."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from ..budget.charge import BudgetCharge
from ..context import AttemptBinding
from ..context.policy import require
from ..providers.capture import CapturedOutput, Observation, unknown_usage
from ..providers.wire import observation_document
from .budget import BudgetLedger
from .execution_state import require_execution_open
from .family_state import lock_request, totals
from .journal import KEY
from .records import verified_observation
from .supervision_deadline import checkpoint_deadline


@dataclass(frozen=True)
class DispatchTicket:
    token: str
    deadline: datetime


class DispatchJournal:
    def __init__(self, engine):
        self.engine = engine
        self.ledger = BudgetLedger(engine)
        self.journal = self.ledger.journal

    def _bound(self, connection, key, principal, binding):
        snapshot = self.journal._request(connection, key, principal)
        require(snapshot is not None, "request_unknown")
        require(snapshot.sha256 == binding.reference().request_sha256, "request_conflict")
        bound = AttemptBinding(snapshot, binding.ordinal)
        policy = self.ledger._policy(connection, key)
        reservation = self.ledger._reservation(connection, key, bound, policy)
        require(reservation is not None, "reservation_unknown")
        return bound, reservation

    @staticmethod
    def _issued(connection, key):
        return connection.execute(text("SELECT *,deadline <= clock_timestamp() AS expired "
            "FROM planning.dispatches WHERE " + KEY + " AND ordinal=:ordinal"), key).mappings().first()

    def issue(self, principal, binding, timeout_seconds):
        require(type(timeout_seconds) is int and 1 <= timeout_seconds <= 86400, "dispatch_timeout")
        reference = binding.reference()
        principal.require("record_attempts", reference.engagement.scope)
        key = {**self.journal._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.begin() as connection:
            membership = lock_request(connection, key)
            bound, _ = self._bound(connection, key, principal, binding)
            if self._issued(connection, key) is not None:
                return None
            require_execution_open(connection, key)
            if membership is not None:
                require(not totals(connection, key, membership["root_engagement_id"])["overage"], "provider_usage_overage")
            overage = connection.execute(text("SELECT EXISTS (SELECT 1 FROM planning.settlements WHERE " + KEY +
                " AND overage UNION ALL SELECT 1 FROM planning.late_observations WHERE " + KEY +
                " AND overage)"), key).scalar_one()
            require(not overage, "provider_usage_overage")
            require(self.journal._attempt(connection, key, bound.request).observation is None,
                    "attempt_already_observed")
            token = str(uuid.uuid4())
            absolute_deadline = checkpoint_deadline(connection, key, principal)
            inserted = connection.execute(text("INSERT INTO planning.dispatches "
                "(tenant_id,project_id,engagement_id,ordinal,token,registered_at,deadline) "
                "SELECT :tenant,:project,:engagement,:ordinal,:token,now,"
                "LEAST(now+make_interval(secs => :seconds),CAST(:absolute_deadline AS timestamptz)) "
                "FROM (SELECT clock_timestamp() AS now) clock "
                "WHERE CAST(:absolute_deadline AS timestamptz) IS NULL OR now < :absolute_deadline "
                "RETURNING token"),
                {**key, "token": token, "seconds": timeout_seconds,
                 "absolute_deadline": absolute_deadline}).scalar_one_or_none()
            require(inserted is not None, "checkpoint_deadline")
            return DispatchTicket(token, self._issued(connection, key)["deadline"])

    def _expire(self, connection, key, bound):
        current = self.journal._attempt(connection, key, bound.request)
        if current.observation is not None:
            return current
        observed = Observation.record(bound, CapturedOutput(b"", False), "unknown", "attempt_deadline",
                                      unknown_usage())
        return self.journal._record(connection, key, bound.request, bound, observed)

    def read_late(self, principal, binding):
        reference = binding.reference()
        principal.require("read_attempts", reference.engagement.scope)
        key = {**self.journal._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.connect() as connection:
            bound, reservation = self._bound(connection, key, principal, binding)
            return self._late(connection, key, bound, reservation)

    @staticmethod
    def _late(connection, key, bound, reservation):
        row = connection.execute(text("SELECT * FROM planning.late_observations WHERE " + KEY +
            " AND ordinal=:ordinal"), key).mappings().first()
        if row is None:
            return None
        wire = observation_document(bytes(row["canonical_bytes"]))
        observed = verified_observation(bound, Observation(
            CapturedOutput(bytes(row["capture_bytes"]), wire.output_complete), bytes(row["canonical_bytes"])))
        charge = BudgetCharge.reconcile(reservation.demand, observed.canonical)
        require((row["input_tokens"], row["output_tokens"], row["accounting_units"], row["overage"]) ==
                (charge.input_tokens, charge.output_tokens, charge.accounting_units, charge.overage),
                "stored_late_charge_corrupt")
        return observed

    def recover(self, principal, binding):
        reference = binding.reference()
        principal.require("record_attempts", reference.engagement.scope)
        key = {**self.journal._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.begin() as connection:
            lock_request(connection, key)
            bound, _ = self._bound(connection, key, principal, binding)
            issued = self._issued(connection, key)
            require(issued is not None, "dispatch_unknown")
            current = self.journal._attempt(connection, key, bound.request)
            if current.observation is not None:
                return current
            require(issued["expired"], "attempt_not_expired")
            return self._expire(connection, key, bound)

    def complete(self, principal, binding, ticket, observation):
        reference = binding.reference()
        principal.require("record_attempts", reference.engagement.scope)
        observation = verified_observation(binding, observation)
        key = {**self.journal._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.begin() as connection:
            lock_request(connection, key)
            bound, reservation = self._bound(connection, key, principal, binding)
            issued = self._issued(connection, key)
            require(issued is not None, "dispatch_unknown")
            require(str(issued["token"]) == ticket.token and issued["deadline"] == ticket.deadline,
                    "dispatch_ticket_mismatch")
            current = self.journal._attempt(connection, key, bound.request)
            if current.observation is None and not issued["expired"]:
                return self.journal._record(connection, key, bound.request, bound, observation)
            current = self._expire(connection, key, bound)
            if current.observation == observation:
                return current
            require(current.observation.document().reason_code == "attempt_deadline", "observation_conflict")
            charge = BudgetCharge.reconcile(reservation.demand, observation.canonical)
            previous = connection.execute(text("SELECT * FROM planning.late_observations WHERE " + KEY +
                " AND ordinal=:ordinal"), key).mappings().first()
            if previous is not None:
                require(bytes(previous["canonical_bytes"]) == observation.canonical and
                        bytes(previous["capture_bytes"]) == observation.capture.content, "late_observation_conflict")
                return current
            connection.execute(text("INSERT INTO planning.late_observations "
                "(tenant_id,project_id,engagement_id,ordinal,canonical_bytes,capture_bytes,"
                "input_tokens,output_tokens,accounting_units,overage) "
                "VALUES (:tenant,:project,:engagement,:ordinal,:content,:capture,:input,:output,:units,:overage)"),
                {**key, "content": observation.canonical, "capture": observation.capture.content,
                 "input": charge.input_tokens, "output": charge.output_tokens, "units": charge.accounting_units,
                 "overage": charge.overage})
            return current
