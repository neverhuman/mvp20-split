from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import (
    JAILGUN_MIN_DEBIT_USD,
    JNOCCIO_MIN_DEBIT_USD,
    MAX_COST_USD,
    MAX_JNOCCIO_ATTEMPTS,
    RESEARCH_RESERVE_USD,
)


class BudgetError(RuntimeError):
    pass


@dataclass(frozen=True)
class BudgetSummary:
    ceiling_usd: float
    debited_usd: float
    reserved_usd: float
    available_usd: float
    jnoccio_attempts: int


class BudgetAccount:
    """Transactional conservative accounting; reported null remains explicit."""

    def __init__(self, path: Path, *, ceiling_usd: float = MAX_COST_USD):
        self.path = path
        self.ceiling_usd = float(ceiling_usd)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS budget_entries (
                    entry_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    state TEXT NOT NULL,
                    reserved_usd REAL NOT NULL,
                    debited_usd REAL,
                    reported_cost_usd REAL,
                    reported_cost_json TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def minimum(kind: str) -> float:
        if kind == "research":
            return RESEARCH_RESERVE_USD
        if kind == "jnoccio":
            return JNOCCIO_MIN_DEBIT_USD
        if kind == "jailgun":
            return JAILGUN_MIN_DEBIT_USD
        raise BudgetError(f"unknown budget kind: {kind}")

    def summary(self) -> BudgetSummary:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(COALESCE(debited_usd,reserved_usd)),0) total,"
                "COALESCE(SUM(CASE WHEN state='reserved' THEN reserved_usd ELSE 0 END),0) reserved,"
                "COALESCE(SUM(CASE WHEN state='debited' THEN debited_usd ELSE 0 END),0) debited,"
                "COALESCE(SUM(CASE WHEN kind='jnoccio' AND state IN ('reserved','debited') "
                "THEN 1 ELSE 0 END),0) attempts FROM budget_entries"
            ).fetchone()
        total = float(row["total"])
        return BudgetSummary(
            ceiling_usd=self.ceiling_usd,
            debited_usd=float(row["debited"]),
            reserved_usd=float(row["reserved"]),
            available_usd=self.ceiling_usd - total,
            jnoccio_attempts=int(row["attempts"]),
        )

    def reserve(self, entry_id: str, kind: str) -> None:
        self.reserve_batch([(entry_id, kind)])

    def reserve_batch(self, entries: list[tuple[str, str]]) -> None:
        """Reserve an entire dispatch or none of it."""

        if len({entry_id for entry_id, _kind in entries}) != len(entries):
            raise BudgetError("budget batch contains duplicate entry IDs")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            new_entries: list[tuple[str, str, float]] = []
            for entry_id, kind in entries:
                existing = connection.execute(
                    "SELECT * FROM budget_entries WHERE entry_id=?", (entry_id,)
                ).fetchone()
                if existing is not None:
                    if existing["kind"] != kind:
                        raise BudgetError(f"budget entry {entry_id} changed kind")
                    continue
                new_entries.append((entry_id, kind, self.minimum(kind)))
            new_jnoccio = sum(kind == "jnoccio" for _entry_id, kind, _amount in new_entries)
            attempts = connection.execute(
                "SELECT COUNT(*) n FROM budget_entries WHERE kind='jnoccio'"
            ).fetchone()["n"]
            if attempts + new_jnoccio > MAX_JNOCCIO_ATTEMPTS:
                raise BudgetError("360-attempt Jnoccio exposure exhausted")
            total = connection.execute(
                "SELECT COALESCE(SUM(COALESCE(debited_usd,reserved_usd)),0) total "
                "FROM budget_entries"
            ).fetchone()["total"]
            reservation = sum(amount for _entry_id, _kind, amount in new_entries)
            if float(total) + reservation > self.ceiling_usd:
                raise BudgetError(
                    f"next dispatch reservation would exceed ${self.ceiling_usd:.2f} ceiling"
                )
            connection.executemany(
                "INSERT INTO budget_entries VALUES(?,?,?,?,?,?,?)",
                [
                    (entry_id, kind, "reserved", amount, None, None, "null")
                    for entry_id, kind, amount in new_entries
                ],
            )

    def settle(self, entry_id: str, reported_cost: Any) -> float:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            entry = connection.execute(
                "SELECT * FROM budget_entries WHERE entry_id=?", (entry_id,)
            ).fetchone()
            if entry is None:
                raise BudgetError(f"budget entry was not reserved: {entry_id}")
            if entry["state"] == "debited":
                return float(entry["debited_usd"])
            numeric = None
            if isinstance(reported_cost, (int, float)) and not isinstance(reported_cost, bool):
                candidate = float(reported_cost)
                if math.isfinite(candidate) and candidate >= 0:
                    numeric = candidate
            debit = max(float(entry["reserved_usd"]), numeric or 0.0)
            other = connection.execute(
                "SELECT COALESCE(SUM(COALESCE(debited_usd,reserved_usd)),0) total "
                "FROM budget_entries WHERE entry_id<>?",
                (entry_id,),
            ).fetchone()["total"]
            if float(other) + debit > self.ceiling_usd:
                raise BudgetError("reported cost would exceed the campaign ceiling")
            connection.execute(
                "UPDATE budget_entries SET state='debited',debited_usd=?,"
                "reported_cost_usd=?,reported_cost_json=? WHERE entry_id=?",
                (
                    debit,
                    numeric,
                    json.dumps(reported_cost, sort_keys=True),
                    entry_id,
                ),
            )
            return debit
