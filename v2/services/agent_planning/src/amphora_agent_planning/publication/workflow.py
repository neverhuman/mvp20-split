"""Bounded publication through the public SDK, outside owner transactions."""

from ..context.policy import require
from .driver import drive_upload


class TracePublisher:
    def __init__(self, journal, reviewer, client):
        self.journal, self.reviewer, self.client = journal, reviewer, client

    def publish(self, principal, publication_id, trace):
        require(self.client.identity.actor_id == principal.actor_id and self.client.identity.scope == principal.scope,
                "publication_client_identity")
        principal.require("read_attempts", principal.scope)
        store = self.journal.store
        store.register(principal, publication_id, trace)
        state = self.journal.read(principal, publication_id)
        if state.attempt is not None and state.attempt.stage in {"finalized", "rejected"}:
            return state
        lease = store.acquire(principal, publication_id, seconds=120)
        try:
            # Re-read after lease acquisition: another worker may have completed
            # between our first read and the acquisition.
            state = self.journal.read(principal, publication_id)
            if state.payload is None:
                stored = store.extractions.read_trace(principal, trace)
                task = store.extractions.read_task(principal, stored.projection.document().task_id)
                review = self.reviewer.review(task.snapshot)
                state = self.journal.prepare(principal, lease, review)
            return self._drive(principal, lease, state)
        finally:
            try:
                store.release(principal, lease)
            except ValueError as error:
                # Expiry is expected during interrupted/slow external calls.
                # Never hide a different persistence/configuration failure.
                if str(error) != "publication_lease_lost":
                    raise

    def _drive(self, principal, lease, state):
        return drive_upload(self.journal, self.client, principal, lease, state)
