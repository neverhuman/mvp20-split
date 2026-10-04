"""Reviewed structural repair policy; uncertainty alone never demands iteration."""

from amphora_contracts_core import Finding

from ..context.policy import require
from ..extraction import TraceProjection
from ..proposals.inputs import ProposalInputs
from ..proposals.validator import GraphCandidateValidator
from ..publication.candidate import PublishedCandidate
from ..repair.feedback import RepairFeedback
from ..research_proposals import ResearchProposalValidator


class NoRepairNeeded(ValueError):
    """The observed output supplies no actionable structural repair request."""


class DiagnosticPolicy:
    def feedback(self, history, sources, questions, knowledge=None):
        rebuilt = TraceProjection.derive(history.projection.document().trace_id,
            history.task, history.observation, history.prior)
        require(rebuilt == history.projection, "result_history_binding")
        observation = history.observation.document()
        if observation.status in {"abstained", "policy_rejected"}:
            raise NoRepairNeeded("diagnostic_terminal_observation")
        if observation.proposal is None:
            findings = (Finding(code="interpretation_output_unavailable", location="/output",
                message="No usable structured output was observed; preserve the prior capture."),)
            withheld = ("/output",)
        else:
            candidate = PublishedCandidate.from_publication(*history.arguments(sources))
            research = ResearchProposalValidator().validate(candidate, questions).document()
            findings, withheld = list(research.findings), set(research.withheld)
            actionable = withheld - {item.location for item in findings if item.code == "question_reference_unavailable"}
            draft = candidate.draft()
            if draft.entities or draft.assertions or getattr(draft, "edits", ()):
                if knowledge is None:
                    # Missing owner context is not something another model call can repair.
                    findings.append(Finding(code="knowledge_context_unavailable", location="/target",
                        message="Graph proposal validation awaits the pinned owner context."))
                else:
                    graph = GraphCandidateValidator().validate(ProposalInputs.from_publication(
                        history.task, history.observation, sources, knowledge, history.interpretation))
                    findings.extend(graph.findings)
                    withheld.update(graph.withheld)
                    actionable.update(graph.withheld)
            if not actionable:
                raise NoRepairNeeded("diagnostic_no_structural_repair")
            findings = tuple({(item.code, item.location, item.message): item for item in findings}.values())
            withheld = tuple(sorted(withheld))
        require(len(findings) <= 256 and len(withheld) <= 256, "diagnostic_feedback_limit")
        return RepairFeedback.create(history.task, history.projection, history.observation,
            findings, withheld_paths=withheld, prior=history.prior)
