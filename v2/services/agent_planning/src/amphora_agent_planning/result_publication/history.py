"""Load exact owned result origins; no peer reads or implicit latest selection."""

from dataclasses import dataclass

from ..context.policy import require
from ..extraction import ExtractionSnapshot, TraceProjection
from ..providers.capture import Observation
from ..publication.journal import PublicationState
from .selection import ResultSelection


@dataclass(frozen=True)
class ResultHistory:
    task: ExtractionSnapshot
    projection: TraceProjection
    observation: Observation
    prior: TraceProjection | None
    interpretation: PublicationState

    @classmethod
    def load(cls, connection, principal, selection, trace_journal):
        selection = ResultSelection.restore(selection.canonical, principal)
        extractions = trace_journal.store.extractions
        stored = extractions._trace(connection, principal, selection.trace())
        require(stored is not None, "result_trace_unknown")
        projection = stored.projection
        document = projection.document()
        task = extractions._task(connection, principal, document.task_id)
        require(task is not None, "result_task_unknown")
        key = extractions.journal._key(document.attempt.engagement) | {"ordinal": document.attempt.ordinal}
        attempt = extractions.journal._attempt(connection, key, task.snapshot.request)
        require(attempt is not None and attempt.observation is not None, "result_observation_unknown")
        prior = None
        if document.prior is not None:
            predecessor = extractions._trace(connection, principal, document.prior)
            require(predecessor is not None, "result_prior_unknown")
            prior = predecessor.projection
        require(TraceProjection.derive(document.trace_id, task.snapshot, attempt.observation, prior).canonical ==
                projection.canonical, "result_history_binding")
        publication = trace_journal._read(connection, principal,
            trace_journal.store.key(principal, selection.document()["interpretation_id"]))
        require(publication is not None and publication.identity.trace() == selection.trace(),
                "result_interpretation_binding")
        require(publication.attempt is not None and publication.attempt.stage == "finalized",
                "interpretation_not_published")
        require(publication.payload.artifact.body == projection.canonical, "result_interpretation_binding")
        return cls(task.snapshot, projection, attempt.observation, prior, publication)

    def arguments(self, review):
        return self.task, self.observation, review, self.interpretation
