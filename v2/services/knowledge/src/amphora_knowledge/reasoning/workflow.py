"""Durable intent, exact historical replay, fresh rights review, then owner result."""

from amphora_contracts_knowledge import EvaluatedReasoning, FailedReasoning

from ..authoring.canonical import KnowledgeError
from ..rebuild.history import RebuildHistory
from ..validation.transport import PeerUnavailable
from .model import ReasoningError


class ReasoningWorkflow:
    def __init__(self, store, profiles, reviewer):
        self.store, self.reviewer = store, reviewer
        self.profiles = {profile.reference: profile for profile in profiles}
        if len(self.profiles) != len(profiles):
            raise KnowledgeError("duplicate_reasoning_profile")
        identities = {(ref.graph, ref.rule_set_id, ref.version) for ref in self.profiles}
        if len(identities) != len(profiles):
            raise KnowledgeError("reasoning_profile_identity_conflict")

    def submit(self, principal, request):
        registered = self.store.begin(principal, request, self.profiles.get(request.rule_set))
        request = registered.document.request
        if registered.status.decision is not None:
            return registered.status
        try:
            history = RebuildHistory(self.store.engine)
            cursor = history.cursor(request.snapshot.graph).through(
                history.tail(request.snapshot.graph, 0, registered.head), registered.head)
            evaluation = registered.profile.evaluate(principal, cursor.state, request)
            included = {item.reference for item in evaluation.inputs.assertions}
            assertions = tuple(item for item in cursor.state.assertions.active() if item.reference in included)
            observation = self.reviewer.review_reasoning(request, assertions)
            decision = EvaluatedReasoning(outcome="evaluated", result=evaluation.to_record(), validation=observation)
        except PeerUnavailable:
            raise
        except (KnowledgeError, ReasoningError) as error:
            decision = FailedReasoning(outcome="failed", code=str(error))
        # Operational peer/SQL failure leaves intent pending. No transaction spans I/O.
        return self.store.finish(registered, decision)

    def read(self, principal, graph, request_id):
        return self.store.read(principal, graph, request_id)
