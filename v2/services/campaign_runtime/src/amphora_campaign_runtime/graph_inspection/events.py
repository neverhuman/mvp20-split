"""Consecutive durable revision invalidations, independent of notification delivery."""

from dataclasses import dataclass

from amphora_contracts_graph_runtime import GraphInvalidation, GraphInvalidationPage
from sqlalchemy import text

from ..lifecycle.claims import RUN
from .policy import ObservedCut, page_limit, read_transaction, require


@dataclass(frozen=True)
class InvalidationWindow:
    previous: int
    current: int
    rows: tuple
    limit: int

    def verified(self):
        require(0 <= self.previous <= self.current)
        expected = self.previous + 1
        for row in self.rows[:self.limit]:
            require(row["revision"] == expected)
            expected += 1
        if len(self.rows) <= self.limit:
            require(expected - 1 == self.current)
        return tuple(GraphInvalidation(event_id=row["event_id"], revision=row["revision"]) for row in self.rows[:self.limit])


class GraphInvalidations:
    def __init__(self, engine, cursors):
        self.engine, self.cursors = engine, cursors

    def page(self, principal, run_id, *, cursor, limit=50):
        page_limit(limit)
        with read_transaction(self.engine) as conn:
            cut = ObservedCut.load(conn, principal, run_id)
            position = self.cursors.decode(cursor, mode="graph-events", scope=principal.scope, resource=run_id)
            require(position.revision <= cut.revision and position.after[1:] == (0, ""))
            params = {**cut.params, "after": position.after[0], "limit": limit + 1}
            rows = tuple(conn.execute(text("SELECT event_id,revision FROM runtime.audit_events WHERE " + RUN +
                " AND ordinal=0 AND revision>:after ORDER BY revision LIMIT :limit"), params).mappings().all())
            entries = InvalidationWindow(position.after[0], cut.revision, rows, limit).verified()
            last = entries[-1].revision if entries else position.after[0]
            continuation = self.cursors.start("graph-events", principal.scope, run_id, cut.revision, (last, 0, ""))
            return GraphInvalidationPage(scope=principal.scope, run_id=run_id, observed_revision=cut.revision,
                entries=entries, next_cursor=self.cursors.encode(continuation), has_more=len(rows) > limit)
