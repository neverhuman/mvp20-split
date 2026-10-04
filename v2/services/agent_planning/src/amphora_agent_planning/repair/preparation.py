"""Fresh bounded public reads before an immutable repair input observation."""

from dataclasses import dataclass

from ..context.policy import require
from ..knowledge_access.transport import KnowledgeReadWindow
from ..proposals.context import KnowledgeContext
from ..research_access.transport import ResearchReadWindow
from ..research_proposals.context import QuestionContext
from ..source_access import SourceReviewer
from ..source_access.artifacts import ArtifactReview
from ..source_access.budget import ReadBudget
from ..source_access.review import ReviewedSources
from .feedback import RepairFeedback
from .history import RepairHistory
from .prompt import RepairPrompt
from .request import RepairRequestPlan


@dataclass(frozen=True)
class PreparedRepair:
    history: RepairHistory
    plan: RepairRequestPlan
    sources: ReviewedSources
    knowledge: KnowledgeContext
    questions: QuestionContext
    packet: bytes


class RepairPreparer:
    def __init__(self, data, knowledge, research=None):
        self.data, self.knowledge, self.research = data, knowledge, research

    def prepare(self, history, feedback_reference, interpretation_reference, *, budget=None):
        budget = ReadBudget() if budget is None else budget
        inputs = ArtifactReview(self.data, history.task.document().scope, budget)
        feedback = RepairFeedback.from_bytes(inputs.artifact(feedback_reference))
        feedback.bind_reference(feedback_reference)
        feedback.verify_history(history.task, history.projection, history.observation, history.prior)
        interpretation = inputs.artifact(interpretation_reference)
        require(interpretation == history.projection.canonical, "repair_interpretation_bytes")
        plan = RepairRequestPlan.build(history.root, history.task, feedback, feedback_reference, interpretation_reference)
        # Reuse the whole-operation deadline, not a fresh allowance for every owner.
        sources = SourceReviewer(self.data).review(plan.task, budget)
        knowledge = self.knowledge.review(plan.task, window=KnowledgeReadWindow(seconds=min(15, budget.remaining_total())))
        if self.research is None:
            gaps = tuple((ref, "research_reader_unconfigured") for ref in plan.task.document().known_questions)
            questions = QuestionContext.bind(plan.task, (), gaps)
        else:
            questions = self.research.review(plan.task, window=ResearchReadWindow(seconds=min(15, budget.remaining_total())))
        packet = RepairPrompt.render(plan, sources, knowledge, questions)
        budget.remaining_total()
        return PreparedRepair(history, plan, sources, knowledge, questions, packet)
