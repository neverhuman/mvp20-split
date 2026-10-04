"""One bounded pass over owned candidates; failures stay local to their effects."""

from dataclasses import dataclass

from amphora_tool_protocol import TransportLost

from ..context.policy import require
from ..providers.profiles import OutputProfiles
from ..research_proposals import QuestionContext
from ..result_publication.journal import ResultState
from ..result_publication.selection import ResultSelection
from .history import HandoffHistory
from .journal import HandoffState
from .selection import HandoffSelection


@dataclass(frozen=True)
class CandidateSlot:
    kind: str
    local_id: str


@dataclass(frozen=True)
class EffectReport:
    slot: CandidateSlot
    state: HandoffState | ResultState | None
    reason: str | None = None

    @property
    def status(self):
        if self.state is None:
            return "blocked"
        if isinstance(self.state, HandoffState):
            return "unprepared" if self.state.progress is None else self.state.progress.state
        return "unprepared" if self.state.attempt is None else self.state.attempt.stage


@dataclass(frozen=True)
class HandoffReport:
    effects: tuple[EffectReport, ...]
    reason: str | None = None


def effect_failure(error):
    if isinstance(error, PermissionError):
        return "access_denied"
    if isinstance(error, TransportLost):
        return "result_uncertain"
    code = str(error)
    if code in {"handoff_lease_unavailable", "result_lease_unavailable"}:
        return "busy"
    if code in {"handoff_selection_conflict", "handoff_configuration_conflict", "result_selection_conflict",
                "result_configuration_conflict"}:
        return "identity_conflict"
    return "effect_unavailable"


class HandoffCoordinator:
    def __init__(self, traces, *, research=None, knowledge=None, answers=None, questions=None):
        self.traces, self.research, self.knowledge = traces, research, knowledge
        self.answers, self.questions = answers, questions

    def run(self, principal, trace, interpretation_id):
        origin = HandoffSelection.bind(principal, trace, interpretation_id, "graph", "graph", "origin-reader")
        with self.traces.store.engine.begin() as connection:
            history = HandoffHistory.load(connection, principal, origin, self.traces)
        observed = history.observation.document()
        if observed.proposal is None:
            return HandoffReport((), "interpretation_unavailable")
        draft = OutputProfiles.draft_model(history.task.request.document().context.output_schema).model_validate_json(
            observed.proposal.payload_json)
        if draft.action == "abstain":
            return HandoffReport((), "abstained")
        results = []
        for kind, items in (("question", draft.questions), ("need", draft.evidence_needs), ("answer", draft.answers)):
            # Duplicates share one slot and are withheld by the existing validators.
            for local in dict.fromkeys(item.local_id for item in items):
                slot = CandidateSlot(kind, local)
                try:
                    if kind == "answer":
                        matches = [item for item in items if item.local_id == local]
                        result = EffectReport(slot, None, "candidate_unavailable") if len(matches) != 1 else self._answer(
                            principal, origin, history, slot, matches[0])
                    else:
                        result = self._owner(principal, origin, slot, self.research)
                except (ValueError, PermissionError, TransportLost) as error:
                    result = EffectReport(slot, None, effect_failure(error))
                results.append(result)
        if draft.entities or draft.assertions or getattr(draft, "edits", ()):
            slot = CandidateSlot("graph", "graph")
            try:
                result = self._owner(principal, origin, slot, self.knowledge)
            except (ValueError, PermissionError, TransportLost) as error:
                result = EffectReport(slot, None, effect_failure(error))
            results.append(result)
        require(len(results) <= 97, "handoff_candidate_limit")
        return HandoffReport(tuple(results))

    @staticmethod
    def _owner(principal, origin, slot, owner):
        if owner is None:
            return EffectReport(slot, None, "owner_unconfigured")
        selection = HandoffSelection.bind(principal, origin.trace(), origin.document()["interpretation_id"],
            slot.kind, slot.local_id, owner.journal.store.owner_id)
        result = owner.submit(principal, selection)
        return EffectReport(slot, result.state, result.reason)

    def _question_ready(self, principal, origin, history, answer):
        if answer.question_local_id is not None:
            if self.research is None:
                return False
            selected = HandoffSelection.bind(principal, origin.trace(), origin.document()["interpretation_id"],
                "question", answer.question_local_id, self.research.journal.store.owner_id)
            state = self.research.journal.read(principal, selected.effect_id)
            return state is not None and state.selection == selected and state.terminal and state.progress.state == "acknowledged"
        if answer.question not in history.task.document().known_questions or self.questions is None:
            return False
        context = self.questions.review(history.task)
        require(context.task_sha256 == history.task.sha256, "research_context_task_binding")
        context = QuestionContext.bind(history.task, context.documents(), context.unavailable())
        return answer.question in context.index()

    def _answer(self, principal, origin, history, slot, answer):
        if self.answers is None:
            return EffectReport(slot, None, "owner_unconfigured")
        selected = ResultSelection.bind(principal, origin.trace(), origin.document()["interpretation_id"],
            "answer", slot.local_id, self.answers.journal.store.publisher_id)
        state = self.answers.journal.read(principal, selected.publication_id)
        if state is not None and state.attempt is not None and state.attempt.stage in {"finalized", "rejected"}:
            return EffectReport(slot, state)
        if not self._question_ready(principal, origin, history, answer):
            return EffectReport(slot, state, "dependency_unavailable")
        return EffectReport(slot, self.answers.publish(principal, selected))
