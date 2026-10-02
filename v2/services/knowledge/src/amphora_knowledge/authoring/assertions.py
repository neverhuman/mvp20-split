"""Immutable assertion corrections and tombstones; disagreements are never averaged."""

from dataclasses import dataclass

from amphora_contracts_knowledge import AssertionRetraction, DomainAssertion

from .canonical import KnowledgeError


@dataclass(frozen=True)
class AssertionHistory:
    records: tuple[DomainAssertion, ...] = ()
    retractions: tuple[AssertionRetraction, ...] = ()

    def current(self, reference):
        record = next((r for r in self.records if r.reference == reference), None)
        if record is None:
            raise KnowledgeError("unknown_assertion_revision")
        if any(r.reference.assertion_id == reference.assertion_id and r.reference.revision > reference.revision
               for r in self.records):
            raise KnowledgeError("stale_assertion_revision")
        if any(r.assertion == reference for r in self.retractions):
            raise KnowledgeError("assertion_retracted")
        return record

    def add(self, record):
        if any(r.reference.assertion_id == record.reference.assertion_id for r in self.records):
            raise KnowledgeError("assertion_identity_reuse")
        if record.reference.revision != 1 or record.supersedes is not None:
            raise KnowledgeError("invalid_assertion_genesis")
        return AssertionHistory(self.records + (record,), self.retractions)

    def correct(self, prior, replacement):
        self.current(prior)
        if (replacement.supersedes != prior or replacement.reference.graph != prior.graph
                or replacement.reference.assertion_id != prior.assertion_id or replacement.reference.revision != prior.revision + 1):
            raise KnowledgeError("invalid_assertion_successor")
        return AssertionHistory(self.records + (replacement,), self.retractions)

    def retract(self, reference, change_id):
        self.current(reference)
        tombstone = AssertionRetraction(assertion=reference, change_id=change_id)
        return AssertionHistory(self.records, self.retractions + (tombstone,))

    def active(self):
        latest = {}
        for record in self.records:
            identity = record.reference.assertion_id
            if identity not in latest or record.reference.revision > latest[identity].reference.revision:
                latest[identity] = record
        retired = {r.assertion for r in self.retractions}
        return tuple(latest[key] for key in sorted(latest) if latest[key].reference not in retired)
