"""Graph-specific facts layered over shared published interpretation binding."""

from dataclasses import dataclass, fields

from ..context.policy import require
from ..publication.candidate import PublishedCandidate
from .context import KnowledgeContext


@dataclass(frozen=True)
class ProposalInputs(PublishedCandidate):
    knowledge: KnowledgeContext

    @classmethod
    def from_publication(cls, task, observation, review, knowledge, publication):
        candidate = PublishedCandidate.from_publication(task, observation, review, publication)
        require(knowledge.task_sha256 == candidate.task.sha256, "validation_graph_binding")
        knowledge = KnowledgeContext.bind(candidate.task, knowledge.profile(), knowledge.snapshot())
        return cls(**{field.name: getattr(candidate, field.name) for field in fields(PublishedCandidate)},
                   knowledge=knowledge)
