"""Persist intent before peer reads; commit only server-issued observations."""

from ..authoring.canonical import KnowledgeError
from .transport import PeerUnavailable


class AuthoringWorkflow:
    def __init__(self, ledger, reviewer):
        self.ledger, self.reviewer = ledger, reviewer

    def submit(self, principal, proposal):
        started = self.ledger.begin(principal, proposal)
        if started.decision is not None:
            return started.decision
        try:
            observation = self.reviewer.review(proposal)
        except PeerUnavailable:
            raise
        except KnowledgeError as error:
            return self.ledger.reject(principal, proposal, str(error))
        return self.ledger.accept(principal, proposal, observation)
