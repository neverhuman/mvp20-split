"""Scoped immutable scientific records; attribution checks stay at the owner boundary."""
from ..observations.intake_store import LabIntakeStore
from ..persistence.decision_journal import DecisionJournal
from ..scientific_publication.artifact import ScientificArtifact
from ..transport.access import AccessDenied
from .boundary import require


class ScientificRecords:
    def __init__(self, engine):
        self.lab = LabIntakeStore(engine)
        self.decisions = DecisionJournal(engine)

    def decision(self, principal, reference):
        result = self.decisions.read(principal.scope,reference)
        if result is not None and result.actor_id != principal.actor_id:
            raise AccessDenied("access_denied")
        return result

    def artifact(self, principal, selection):
        if selection.kind == "lab-intake":
            require(selection.scope == principal.scope,"scientific_selection_scope")
            stored = self.lab.read(principal.scope,principal.actor_id,selection.intake_id)
            require(stored is not None,"scientific_record_missing")
            return ScientificArtifact.from_intake(stored)
        result = self.decision(principal,selection.reference)
        require(result is not None,"scientific_record_missing")
        return ScientificArtifact.from_decision(result)


def selection_scope(selection):
    return selection.scope if selection.kind == "lab-intake" else selection.reference.scope
