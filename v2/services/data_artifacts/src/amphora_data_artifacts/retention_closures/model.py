"""Canonical membership identity; no storage, rights grant or Runtime authority."""

import hashlib
import json
from dataclasses import dataclass
from functools import cached_property

from amphora_contracts_core import ArtifactRef

from ..publication.model import UploadError


@dataclass(frozen=True)
class ProtectedClosure:
    root: ArtifactRef
    members: tuple[ArtifactRef, ...]

    def __post_init__(self):
        if type(self.members) is not tuple or not 1 <= len(self.members) <= 4096:
            raise UploadError("retention_closure_limit")
        root = ArtifactRef.model_validate_json(self.root.model_dump_json())
        members = tuple(ArtifactRef.model_validate_json(r.model_dump_json()) for r in self.members)
        identifiers = tuple(r.artifact_id for r in members)
        if identifiers != tuple(sorted(set(identifiers))):
            raise UploadError("retention_closure_order_or_duplicate")
        if root not in members or any(r.scope != root.scope for r in members):
            raise UploadError("retention_closure_binding")
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "members", members)

    @cached_property
    def digest(self):
        body = json.dumps([r.model_dump(mode="json") for r in self.members], sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        return hashlib.sha256(b"amphora.artifact-retention/derived-closure-v1\0" + body).hexdigest()
