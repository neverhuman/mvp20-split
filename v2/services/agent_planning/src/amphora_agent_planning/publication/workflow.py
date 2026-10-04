"""Bounded publication through the public SDK, outside owner transactions."""

from amphora_tool_protocol import CommandRejected

from ..context.policy import require


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
        store = self.journal.store

        def guard():
            store.guard(principal, lease)

        def advance(action, data=None):
            return self.journal.advance(principal, lease, state.position, action, data)

        # One invocation can recover an abandoned upload and finish one successor.
        # It does not spend all eight attempts retrying a failing peer.
        for _ in range(10):
            attempt, artifact = state.attempt, state.payload.artifact
            if attempt.stage in {"finalized", "rejected"}:
                return state
            guard()
            if attempt.stage == "prepared":
                try:
                    receipt = self.client.begin_derived(artifact.content, artifact.declaration,
                        attempt.identity.begin_id, guard=guard, resume=True)
                except CommandRejected as error:
                    state = advance("rejected", {"reason": error.reason_code})
                else:
                    state = advance("begun", receipt.model_dump(mode="json"))
            elif attempt.stage == "begun":
                # Only this successful CAS authorizes this invocation's single PUT.
                # A crash immediately after CAS is conservatively uncertain.
                state = advance("streaming")
                receipt = self.client.stream(state.attempt.upload.upload, artifact.body, guard=guard)
                state = advance("streamed", receipt.model_dump(mode="json"))
            elif attempt.stage == "streaming":
                state = advance("abandoned")
            elif attempt.stage == "abandoned":
                state = advance("replacement")
            elif attempt.stage == "streamed":
                state = advance("finalizing")
            elif attempt.stage == "finalizing":
                try:
                    receipt = self.client.finalize(attempt.upload.upload, attempt.identity.finalize_id,
                                                   guard=guard, resume=True)
                except CommandRejected as error:
                    state = advance("rejected", {"reason": error.reason_code})
                else:
                    derivation = self.client.derivation(receipt.artifact)
                    state = advance("finalized", {"receipt": receipt.model_dump(mode="json"),
                                                   "derivation": derivation.model_dump(mode="json")})
        raise ValueError("publication_transition_limit")
