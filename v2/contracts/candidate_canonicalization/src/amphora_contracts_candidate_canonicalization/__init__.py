"""Encoding evidence, never source authentication or evaluation reuse permission."""
from typing import Literal

from amphora_contracts_core import Digest, SchemaRef, Scope, WireModel


class CanonicalCandidate(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic_encoding"]
    scope: Scope
    kind: Literal["numeric", "polymer", "sequence"]
    semantic_profile: SchemaRef
    equivalence_profile: SchemaRef
    source_sha256: Digest
    canonical_sha256: Digest


__all__ = ["CanonicalCandidate"]
