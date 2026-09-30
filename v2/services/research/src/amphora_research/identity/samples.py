"""Identity matching preserves unknowns; it never creates candidate/sample rows."""

from dataclasses import dataclass
from typing import Literal

from amphora_contracts_research import (
    CandidateRevision,
    CandidateRevisionRef,
    SampleIdentity,
    SampleRevisionRef,
)

from .questions import ResearchIdentityError


@dataclass(frozen=True)
class CandidateDefinition:
    record: CandidateRevision

    def __post_init__(self) -> None:
        record = self.record
        if record.reference.scope != record.representation.scope:
            raise ResearchIdentityError("representation_scope_mismatch")
        prior = record.supersedes
        ref = record.reference
        if prior is None:
            if ref.revision != 1:
                raise ResearchIdentityError("missing_predecessor")
        elif prior.scope != ref.scope or prior.candidate_id != ref.candidate_id or prior.revision + 1 != ref.revision:
            raise ResearchIdentityError("invalid_predecessor")


@dataclass(frozen=True)
class SampleDefinition:
    record: SampleIdentity

    def __post_init__(self) -> None:
        record = self.record
        scope = record.reference.scope
        if record.candidate.scope != scope or record.identity_evidence.scope != scope:
            raise ResearchIdentityError("sample_scope_mismatch")
        if record.material_state is not None and record.material_state.scope != scope:
            raise ResearchIdentityError("material_state_scope_mismatch")
        prior = record.supersedes
        ref = record.reference
        if prior is None:
            if ref.revision != 1:
                raise ResearchIdentityError("missing_predecessor")
        elif prior.scope != ref.scope or prior.sample_id != ref.sample_id or prior.revision + 1 != ref.revision:
            raise ResearchIdentityError("invalid_predecessor")


@dataclass(frozen=True)
class IdentityMatch:
    disposition: Literal["matched", "quarantined"]
    reason: str

    @classmethod
    def reconcile(
        cls, candidate_ref: CandidateRevisionRef, sample_ref: SampleRevisionRef,
        candidate: CandidateDefinition | None, sample: SampleDefinition | None,
    ) -> "IdentityMatch":
        if candidate_ref.scope != sample_ref.scope:
            return cls("quarantined", "scope_mismatch")
        if candidate is None:
            return cls("quarantined", "unknown_candidate")
        if sample is None:
            return cls("quarantined", "unknown_sample")
        if candidate.record.reference != candidate_ref:
            return cls("quarantined", "candidate_revision_mismatch")
        if sample.record.reference != sample_ref:
            return cls("quarantined", "sample_revision_mismatch")
        if sample.record.candidate != candidate_ref:
            return cls("quarantined", "sample_candidate_mismatch")
        return cls("matched", "exact_identity_only")
