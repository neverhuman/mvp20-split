"""An immutable retained retrieval selection, never a command to rerun retrieval."""

import json
import re
from dataclasses import dataclass

from amphora_contracts_representations import RetrieveRepresentations

from ..context import RequestSnapshot
from ..context.policy import require
from .identity import canonical, fingerprint, policy


@dataclass(frozen=True)
class RetrievalSelection:
    request: RequestSnapshot
    canonical: bytes
    result_sha256: str

    @classmethod
    def bind(cls, request, query, result_sha256):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {"campaign_proposal", "supervision"}, "retrieval_context_purpose")
        require(type(result_sha256) is str and re.fullmatch(r"[0-9a-f]{64}", result_sha256) is not None,
                "retrieval_context_result_pin")
        query = RetrieveRepresentations.model_validate(query.model_dump(mode="python", warnings=False))
        require(query.generation.scope == query.query.scope == original.reference.scope, "retrieval_context_scope")
        query = query.model_copy(update={"policy": policy(query.policy, original.reference.scope)})
        return cls(request, canonical(query.model_dump(mode="json")), result_sha256)

    def document(self):
        require(type(self.canonical) is bytes and 0 < len(self.canonical) <= 4194304, "retrieval_context_size")
        return RetrieveRepresentations.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return fingerprint({"format": "planning.retrieval-selection.v1", "request_sha256": self.request.sha256,
                            "query": json.loads(self.canonical), "result_sha256": self.result_sha256})
