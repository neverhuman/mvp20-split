"""Original campaign-bound Artifact identities, without claiming access permission."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef

from ..context import RequestSnapshot
from ..context.policy import require


@dataclass(frozen=True)
class ArtifactSelection:
    request: RequestSnapshot
    canonical: bytes

    @classmethod
    def bind(cls, request, references):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {"campaign_proposal", "supervision"}, "campaign_artifact_purpose")
        require(type(references) is tuple and len(references) <= 128, "campaign_artifact_count")
        references = tuple(ArtifactRef.model_validate(ref.model_dump(mode="python", warnings=False)) for ref in references)
        require(all(ref.scope == original.reference.scope for ref in references), "campaign_artifact_scope")
        require(len({ref.artifact_id for ref in references}) == len(references), "campaign_artifact_duplicate")
        require(all(ref.size_bytes <= 4194304 for ref in references), "campaign_artifact_size")
        raw = json.dumps([ref.model_dump(mode="json") for ref in references], sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
        require(len(raw) <= 262144, "campaign_artifact_selection_size")
        return cls(request, raw)

    def references(self):
        require(type(self.canonical) is bytes and len(self.canonical) <= 262144, "campaign_artifact_selection_size")
        values = json.loads(self.canonical)
        require(type(values) is list and len(values) <= 128, "campaign_artifact_count")
        return tuple(ArtifactRef.model_validate_json(json.dumps(value)) for value in values)

    @property
    def sha256(self):
        return hashlib.sha256(b"planning-campaign-artifacts.v1\n" + self.request.sha256.encode("ascii") + b"\n" + self.canonical).hexdigest()
