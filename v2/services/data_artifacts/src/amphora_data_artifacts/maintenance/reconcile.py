"""Explicit bounded sweep; persistent reservation state is the retry queue."""

import json
import time
import uuid

from amphora_contracts_artifacts import parse_command
from sqlalchemy import text

from ..publication.model import UploadError
from ..publication.uploads import SCOPE
from ..retention.outcomes import OutcomeUnavailable


class Reconciler:
    def __init__(self, reservations):
        self.reservations = reservations

    def sweep(self, principal, *, limit=20, after="", seconds=30):
        principal.require("retention")
        if not 1 <= limit <= 100 or not 1 <= seconds <= 300:
            raise ValueError("Bounded sweep required")
        deadline = time.monotonic() + seconds
        with self.reservations.commands.engine.connect() as conn:
            ids = conn.execute(text("SELECT reservation_id FROM artifacts.reservations WHERE " + SCOPE +
                " AND runtime_owner=:actor AND status='reserved' AND reservation_id>:after "
                "ORDER BY reservation_id LIMIT :limit"),
                {**principal.bindings, "after": after, "limit": limit}).scalars().all()
        result = {"confirmed": 0, "released": 0, "deferred": 0, "conflicts": 0, "next_cursor": ""}
        for index, reservation_id in enumerate(ids):
            if time.monotonic() >= deadline:
                result["next_cursor"] = ids[index - 1] if index else after
                break
            command = parse_command("artifacts.reconcile", json.dumps({"identity": {
                "command_family": "artifacts.reconcile", "command_id": uuid.uuid5(uuid.NAMESPACE_URL,
                    "amphora-reconcile:" + reservation_id).hex,
                "actor_id": principal.actor_id, "scope": principal.scope.model_dump()},
                "payload": {"reservation_id": reservation_id}}))
            try:
                receipt = self.reservations.reconcile(principal, command)
                result[receipt.outcome.status] += 1
            except OutcomeUnavailable:
                result["deferred"] += 1
            except UploadError:
                result["conflicts"] += 1
            result["next_cursor"] = reservation_id if len(ids) == limit else ""
        return result
