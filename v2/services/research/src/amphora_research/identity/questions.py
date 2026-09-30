"""Question and evidence-need invariants stay with their Research owner."""

from dataclasses import dataclass

from amphora_contracts_research import EvidenceNeed, ResearchQuestion


class ResearchIdentityError(ValueError):
    """Safe bounded code without source document content."""


@dataclass(frozen=True)
class QuestionDefinition:
    record: ResearchQuestion

    def __post_init__(self) -> None:
        record = self.record
        if record.applicability.scope != record.reference.scope:
            raise ResearchIdentityError("applicability_scope_mismatch")
        criteria = [criterion.criterion_id for criterion in record.criteria]
        if len(criteria) != len(set(criteria)):
            raise ResearchIdentityError("duplicate_criterion")
        previous = record.supersedes
        reference = record.reference
        if previous is None:
            if reference.revision != 1:
                raise ResearchIdentityError("missing_predecessor")
        elif (previous.scope != reference.scope or previous.question_id != reference.question_id
              or previous.revision + 1 != reference.revision):
            raise ResearchIdentityError("invalid_predecessor")

    def bind_need(self, need: EvidenceNeed) -> "BoundEvidenceNeed":
        if need.question != self.record.reference:
            raise ResearchIdentityError("question_revision_mismatch")
        if need.reference.scope != self.record.reference.scope or need.required_context.scope != need.reference.scope:
            raise ResearchIdentityError("need_scope_mismatch")
        requested = set(need.criterion_ids)
        if len(requested) != len(need.criterion_ids):
            raise ResearchIdentityError("duplicate_criterion")
        if not requested <= {criterion.criterion_id for criterion in self.record.criteria}:
            raise ResearchIdentityError("unknown_criterion")
        previous = need.supersedes
        reference = need.reference
        if previous is None:
            if reference.revision != 1:
                raise ResearchIdentityError("missing_predecessor")
        elif (previous.scope != reference.scope or previous.need_id != reference.need_id
              or previous.revision + 1 != reference.revision):
            raise ResearchIdentityError("invalid_predecessor")
        return BoundEvidenceNeed(need)


@dataclass(frozen=True)
class BoundEvidenceNeed:
    """Question-bound declaration; no observation or acceptance is implied."""

    record: EvidenceNeed
