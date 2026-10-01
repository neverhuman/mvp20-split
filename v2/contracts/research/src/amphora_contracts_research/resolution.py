"""Scoped identity lookup is a read, not scientific or execution acceptance."""

from typing import Literal

from amphora_contracts_core import Scope, WireModel

from .identity import CandidateRevisionRef, SampleRevisionRef


class ResolveIdentity(WireModel):
    wire_version: Literal["1"]
    scope: Scope
    candidate: CandidateRevisionRef
    sample: SampleRevisionRef


class IdentityResolution(WireModel):
    wire_version: Literal["1"]
    scope: Scope
    candidate: CandidateRevisionRef
    sample: SampleRevisionRef
    disposition: Literal["matched", "quarantined"]
    reason: Literal["scope_mismatch", "unknown_candidate", "unknown_sample", "candidate_revision_mismatch",
                    "sample_revision_mismatch", "sample_candidate_mismatch", "exact_identity_only"]
    authority: Literal["identity_only"]
