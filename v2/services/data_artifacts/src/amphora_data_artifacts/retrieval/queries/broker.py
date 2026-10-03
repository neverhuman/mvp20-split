"""Recoverable read-only backend queries; PostgreSQL alone publishes immutable results."""

from amphora_contracts_representations import RetrieveRepresentations

from ...representations.mapping import _validated
from ...representations.storage.records import authorize
from ...source_rights.ledger import SourceRights
from ..validation import require
from . import storage
from .access import QueryAccess, authorize_history
from .execution import execute
from .mapping import record_to_wire


class RetrievalBroker:
    def __init__(self, reads, backend):
        self.reads = reads
        self.engine = reads.engine
        self.backend = backend

    @staticmethod
    def _authorize(principal):
        authorize(principal, "representation_read")
        principal.require("read")

    def retrieve(self, principal, request):
        self._authorize(principal)
        request = _validated(request, RetrieveRepresentations)
        with self.engine.begin() as connection:
            SourceRights.lock(connection, principal)
            key = storage.lock_query(connection, principal, request.retrieval_id)
            plan, proof = storage.resolve(connection, principal, request)
            row = storage.intent(connection, key)
            if row is not None:
                storage.require_intent(row, plan, request)
                previous = storage.result(connection, key, plan)
                if previous is not None:
                    authorize_history(connection, principal, previous)
                    return record_to_wire(previous)
            access = QueryAccess.capture(connection, principal, plan)
            require(self.backend.reference == plan.generation.backend_profile, "retrieval_backend_profile")
            if row is None:
                storage.admit(connection, key, plan, request)
        # No owner SQL lock/transaction spans filesystem or backend I/O.
        candidate = execute(principal, plan, proof, access, self.reads, self.backend)
        with self.engine.begin() as connection:
            SourceRights.lock(connection, principal)
            storage.lock_query(connection, principal, request.retrieval_id)
            storage.require_intent(storage.intent(connection, key), plan, request)
            previous = storage.result(connection, key, plan)
            if previous is not None:
                authorize_history(connection, principal, previous)
                return record_to_wire(previous)
            access.fence(connection, principal, plan)
            storage.save(connection, key, candidate, access)
            return record_to_wire(candidate)

    def read(self, principal, retrieval_id):
        self._authorize(principal)
        with self.engine.begin() as connection:
            SourceRights.lock(connection, principal)
            key = storage.key_for_query(principal, retrieval_id)
            row = storage.intent(connection, key)
            require(row is not None, "retrieval_query_missing")
            request = RetrieveRepresentations.model_validate_json(bytes(row["request_bytes"]))
            plan, _ = storage.resolve(connection, principal, request)
            storage.require_intent(row, plan, request)
            value = storage.result(connection, key, plan)
            require(value is not None, "retrieval_query_pending")
            authorize_history(connection, principal, value)
            return record_to_wire(value)
