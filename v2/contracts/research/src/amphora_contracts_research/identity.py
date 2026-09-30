"""Scientific identities stay distinct even when nominal structures match."""

from typing import Literal

from amphora_contracts_core import ArtifactRef, Identifier, SafePositiveInt, Scope, WireModel


class CandidateRevisionRef(WireModel):
    scope: Scope
    candidate_id: Identifier
    revision: SafePositiveInt


class MaterialStateRevisionRef(WireModel):
    scope: Scope
    material_state_id: Identifier
    revision: SafePositiveInt


class SampleRevisionRef(WireModel):
    scope: Scope
    sample_id: Identifier
    revision: SafePositiveInt


class CandidateRevision(WireModel):
    wire_version: Literal["1"]
    reference: CandidateRevisionRef
    representation: ArtifactRef
    supersedes: CandidateRevisionRef | None


class SampleIdentity(WireModel):
    wire_version: Literal["1"]
    reference: SampleRevisionRef
    candidate: CandidateRevisionRef
    material_state: MaterialStateRevisionRef | None
    identity_evidence: ArtifactRef
    supersedes: SampleRevisionRef | None
