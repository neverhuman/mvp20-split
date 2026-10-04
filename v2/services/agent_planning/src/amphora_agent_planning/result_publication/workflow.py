"""Result-specific preparation with the bounded public Data upload driver."""

from dataclasses import dataclass

from ..context.policy import require
from ..publication.driver import drive_upload
from ..repair.feedback import RepairFeedback
from ..research_proposals import QuestionContext
from ..source_access.review import ReviewedSources
from .history import ResultHistory


@dataclass(frozen=True)
class ResultInputs:
    sources: ReviewedSources
    questions: QuestionContext | None = None
    feedback: RepairFeedback | None = None


class ResultPublisher:
    def __init__(self, journal, preparer, client):
        self.journal, self.preparer, self.client = journal, preparer, client

    def publish(self, principal, selection):
        require(self.client.identity.actor_id == principal.actor_id and self.client.identity.scope == principal.scope,
                "result_client_identity")
        principal.require("read_attempts", principal.scope)
        store = self.journal.store
        selected = store.register(principal, selection)
        publication_id = selected.publication_id
        state = self.journal.read(principal, publication_id)
        if state.attempt is not None and state.attempt.stage in {"finalized", "rejected"}:
            return state
        lease = store.acquire(principal, publication_id, seconds=120)
        try:
            state = self.journal.read(principal, publication_id)
            if state.payload is None:
                with store.engine.begin() as connection:
                    history = ResultHistory.load(connection, principal, selected, store.traces)
                # The configured input reviewer consumes permitted public inputs
                # outside SQL. It cannot supply arbitrary result payload bytes.
                inputs = self.preparer.prepare(history, selected)
                require(isinstance(inputs, ResultInputs), "result_preparer_contract")
                state = self.journal.prepare(principal, lease, inputs.sources,
                                            questions=inputs.questions, feedback=inputs.feedback)
            return drive_upload(self.journal, self.client, principal, lease, state)
        finally:
            try:
                store.release(principal, lease)
            except ValueError as error:
                if str(error) != "result_lease_lost":
                    raise
