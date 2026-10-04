"""Immutable charge settlement; provider observations remain unchanged."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from ..budget.charge import BudgetCharge
from ..context import AttemptBinding
from ..context.policy import require
from .budget import BudgetLedger
from .family_state import lock_request
from .journal import KEY


@dataclass(frozen=True)
class BudgetSettlement:
    charge: BudgetCharge
    registered_at: datetime


class SettlementJournal:
    def __init__(self, engine):
        self.engine = engine
        self.ledger = BudgetLedger(engine)
        self.journal = self.ledger.journal

    def _charge(self, connection, key, binding):
        policy = self.ledger._policy(connection, key)
        reservation = self.ledger._reservation(connection, key, binding, policy)
        require(reservation is not None, "reservation_unknown")
        attempt = self.journal._attempt(connection, key, binding.request)
        require(attempt.observation is not None, "attempt_pending")
        return BudgetCharge.reconcile(reservation.demand, attempt.observation.canonical)

    @staticmethod
    def _read(connection, key, charge):
        row = connection.execute(text("SELECT * FROM planning.settlements WHERE " + KEY +
            " AND ordinal=:ordinal"), key).mappings().first()
        if row is None:
            return None
        require((row["observation_sha256"], row["input_tokens"], row["output_tokens"], row["accounting_units"],
                 row["overage"], row["charge_profile"]) ==
                (charge.observation_sha256, charge.input_tokens, charge.output_tokens,
                 charge.accounting_units, charge.overage, "reserved_floor_v1"), "stored_settlement_corrupt")
        return BudgetSettlement(charge, row["registered_at"])

    def settle(self, principal, binding):
        reference = binding.reference()
        principal.require("record_attempts", reference.engagement.scope)
        key = {**self.journal._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.begin() as connection:
            lock_request(connection, key)
            snapshot = self.journal._request(connection, key, principal)
            require(snapshot is not None, "request_unknown")
            require(snapshot.sha256 == reference.request_sha256, "request_conflict")
            charge = self._charge(connection, key, AttemptBinding(snapshot, reference.ordinal))
            existing = self._read(connection, key, charge)
            if existing is not None:
                return existing
            connection.execute(text("INSERT INTO planning.settlements "
                "(tenant_id,project_id,engagement_id,ordinal,observation_sha256,charge_profile,"
                "input_tokens,output_tokens,accounting_units,overage) "
                "VALUES (:tenant,:project,:engagement,:ordinal,:digest,'reserved_floor_v1',"
                ":input,:output,:units,:overage)"), {**key, "digest": charge.observation_sha256,
                "input": charge.input_tokens, "output": charge.output_tokens,
                "units": charge.accounting_units, "overage": charge.overage})
            return self._read(connection, key, charge)

    def read(self, principal, reference):
        principal.require("read_attempts", reference.engagement.scope)
        key = {**self.journal._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.connect() as connection:
            snapshot = self.journal._request(connection, key, principal)
            if snapshot is None:
                return None
            require(snapshot.sha256 == reference.request_sha256, "request_conflict")
            exists = connection.execute(text("SELECT 1 FROM planning.settlements WHERE " + KEY +
                " AND ordinal=:ordinal"), key).first()
            if exists is None:
                return None
            charge = self._charge(connection, key, AttemptBinding(snapshot, reference.ordinal))
            return self._read(connection, key, charge)
