"""Fresh processing observations for one effect; never a durable rights grant."""

from dataclasses import dataclass

from ..context.policy import require
from ..knowledge_access.transport import KnowledgeReadWindow
from ..proposals.context import KnowledgeContext
from ..publication.payload import TraceArtifact
from ..research_access.transport import ResearchReadWindow
from ..research_proposals import QuestionContext
from ..source_access import SourceReviewer
from ..source_access.artifacts import ArtifactReview
from ..source_access.budget import ReadBudget
from ..source_access.review import ReviewedSources


@dataclass(frozen=True)
class HandoffInputs:
    sources: ReviewedSources
    questions: QuestionContext | None = None
    knowledge: KnowledgeContext | None = None


class HandoffPreparer:
    def __init__(self, data, *, research=None, knowledge=None):
        self.data, self.research, self.knowledge = data, research, knowledge

    def _sources(self, history, budget):
        sources = SourceReviewer(self.data).review(history.task, budget)
        artifact = TraceArtifact.reviewed(history.interpretation.identity, history.projection, sources)
        require(artifact == history.interpretation.payload.artifact, "handoff_source_binding")
        reference = history.interpretation.attempt.result.artifact
        body = ArtifactReview(self.data, history.task.document().scope, budget).artifact(reference)
        require(body == history.projection.canonical, "handoff_interpretation_bytes")
        budget.remaining_total()
        return sources

    def prepare(self, history, selection):
        require(history.projection.reference() == selection.trace() and
                history.interpretation.identity.document()["publication_id"] == selection.document()["interpretation_id"],
                "handoff_origin_binding")
        budget = ReadBudget()
        sources = self._sources(history, budget)
        questions = knowledge = None
        if selection.document()["kind"] == "graph":
            require(self.knowledge is not None, "handoff_graph_context_missing")
            knowledge = self.knowledge.review(history.task,
                window=KnowledgeReadWindow(seconds=min(15, budget.remaining_total())))
        elif self.research is None:
            questions = QuestionContext.bind(history.task, (), tuple(
                (ref, "research_reader_unconfigured") for ref in history.task.document().known_questions))
        else:
            questions = self.research.review(history.task,
                window=ResearchReadWindow(seconds=min(15, budget.remaining_total())))
        budget.remaining_total()
        return HandoffInputs(sources, questions, knowledge)

    def authorize(self, history, payload, *, seconds):
        # Current permission only; do not regenerate a prepared graph/request or
        # require fresh scientific acceptance of the original interpretation.
        require(payload.request.selection.trace() == history.projection.reference(), "handoff_origin_binding")
        self._sources(history, ReadBudget(seconds=seconds))
