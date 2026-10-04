"""Fresh public processing reads and exact owner contexts before new result bytes."""

from ..context.policy import require
from ..knowledge_access.transport import KnowledgeReadWindow, KnowledgeUnavailable
from ..publication.candidate import PublishedCandidate
from ..research_access.transport import ResearchReadWindow
from ..research_proposals.context import QuestionContext
from ..source_access import SourceReviewer
from ..source_access.artifacts import ArtifactReview
from ..source_access.budget import ReadBudget
from .diagnostics import DiagnosticPolicy
from .payload import interpretation
from .workflow import ResultInputs


class ResultPreparer:
    def __init__(self, data, *, knowledge=None, research=None):
        self.data, self.knowledge, self.research = data, knowledge, research

    def prepare(self, history, selection, *, budget=None):
        require(history.projection.reference() == selection.trace() and
            history.interpretation.identity.document()["publication_id"] == selection.document()["interpretation_id"],
            "result_preparation_selection")
        budget = ReadBudget() if budget is None else budget
        sources = SourceReviewer(self.data).review(history.task, budget)
        _, reference, _ = interpretation(*history.arguments(sources), prior=history.prior)
        body = ArtifactReview(self.data, history.task.document().scope, budget).artifact(reference)
        require(body == history.projection.canonical, "result_interpretation_bytes")
        if self.research is None:
            gaps = tuple((ref, "research_reader_unconfigured") for ref in history.task.document().known_questions)
            questions = QuestionContext.bind(history.task, (), gaps)
        else:
            questions = self.research.review(history.task,
                window=ResearchReadWindow(seconds=min(15, budget.remaining_total())))
        feedback = None
        if selection.document()["kind"] == "feedback":
            knowledge = None
            if self.knowledge is not None and history.observation.document().proposal is not None:
                draft = PublishedCandidate.from_publication(*history.arguments(sources)).draft()
                if draft.entities or draft.assertions or getattr(draft, "edits", ()):
                    try:
                        knowledge = self.knowledge.review(history.task,
                            window=KnowledgeReadWindow(seconds=min(15, budget.remaining_total())))
                    except KnowledgeUnavailable:
                        # Peer availability is not a model defect. Independent Research
                        # validation can still yield useful structural diagnostics.
                        knowledge = None
            feedback = DiagnosticPolicy().feedback(history, sources, questions, knowledge)
        budget.remaining_total()
        return ResultInputs(sources, questions, feedback)
