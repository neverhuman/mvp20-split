"""Synthesis policy evaluates alternatives before immutable owner-local persistence."""
from ..persistence.decision_document import require
from ..persistence.decision_journal import DecisionJournal, require_candidate
from .decision import prepare


def validate_links(connection, record):
    require_candidate(connection,record.assessment.policy.context.candidate)


class SynthesisStore:
    def __init__(self, engine):
        self.journal = DecisionJournal(engine)

    def assess(self, policy, options, actor, decision_id, *, consumed=()):
        return self.journal.publish(prepare(policy,options,actor,decision_id,consumed=consumed),validate_links)

    def read(self, scope, reference):
        require(reference.kind == "synthesis","synthesis_decision_kind")
        return self.journal.read(scope,reference)
