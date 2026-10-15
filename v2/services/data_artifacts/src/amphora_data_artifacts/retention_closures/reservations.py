"""One atomic group reservation; existing root proof governs every member."""

import json

from amphora_contracts_artifact_retention import DerivedClosureReservationReceipt, ReserveDerivedClosure
from sqlalchemy import text

from ..publication.model import UploadError
from ..publication.uploads import SCOPE
from ..retention.reservations import Reservations
from . import storage


class ClosureReservations(Reservations):
    def reserve(self, principal, command):
        principal.require("retention", command.identity)
        if command.identity.command_family != "artifacts.reserve_derived_closure":
            raise UploadError("wrong_command_family")
        request = ReserveDerivedClosure.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        if request.intent.runtime_owner != principal.actor_id:
            raise UploadError("access_denied")
        self.commands.register(command)

        def reserve(conn):
            # A rejected new request must not leave an ordinary root reservation behind.
            with conn.begin_nested():
                root, created = self._reserve_root(conn, principal, request)
                if created:
                    closure = storage.discover(conn, principal, request.artifact)
                    storage.persist(conn, principal, root, closure)
                elif not conn.execute(text("SELECT EXISTS(SELECT 1 FROM artifacts.retention_closures WHERE " +
                    SCOPE + " AND reservation_id=:reservation)"),
                    {**principal.bindings, "reservation": root.binding.reservation_id}).scalar_one():
                    raise UploadError("reservation_profile_conflict")
                return storage.load(conn, principal, root)
        return self._transaction(principal, command, reserve, receipt_model=DerivedClosureReservationReceipt)

    def get(self, principal, reservation_id):
        principal.require("retention")
        with self.commands.engine.connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY"))
            root = self._load(conn, principal, reservation_id, lock=False)
            return storage.load(conn, principal, root)
