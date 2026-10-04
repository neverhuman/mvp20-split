"""Load exact published origins inside Planning; no peer reads or implicit latest selection."""

from dataclasses import dataclass

from ..context.policy import require
from ..extraction import ExtractionSnapshot, TraceProjection
from ..providers.capture import Observation
from .journal import PublicationState


@dataclass(frozen=True)
class PublishedHistory:
    task: ExtractionSnapshot
    projection: TraceProjection
    observation: Observation
    prior: TraceProjection | None
    interpretation: PublicationState

    @classmethod
    def _load(cls, connection, principal, selection, trace_journal, prefix):
        extractions = trace_journal.store.extractions
        stored = extractions._trace(connection, principal, selection.trace())
        require(stored is not None, f"{prefix}_trace_unknown")
        projection = stored.projection
        document = projection.document()
        task = extractions._task(connection, principal, document.task_id)
        require(task is not None, f"{prefix}_task_unknown")
        key = extractions.journal._key(document.attempt.engagement) | {"ordinal": document.attempt.ordinal}
        attempt = extractions.journal._attempt(connection, key, task.snapshot.request)
        require(attempt is not None and attempt.observation is not None, f"{prefix}_observation_unknown")
        prior = None
        if document.prior is not None:
            predecessor = extractions._trace(connection, principal, document.prior)
            require(predecessor is not None, f"{prefix}_prior_unknown")
            prior = predecessor.projection
        require(TraceProjection.derive(document.trace_id, task.snapshot, attempt.observation, prior).canonical ==
                projection.canonical, f"{prefix}_history_binding")
        publication = trace_journal._read(connection, principal,
            trace_journal.store.key(principal, selection.document()["interpretation_id"]))
        require(publication is not None and publication.identity.trace() == selection.trace(),
                f"{prefix}_interpretation_binding")
        require(publication.attempt is not None and publication.attempt.stage == "finalized",
                "interpretation_not_published")
        require(publication.payload.artifact.body == projection.canonical, f"{prefix}_interpretation_binding")
        return cls(task.snapshot, projection, attempt.observation, prior, publication)
