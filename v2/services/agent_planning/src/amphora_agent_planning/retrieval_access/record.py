"""Exact source/vector provenance and recorded scores, not scientific confidence."""

from dataclasses import dataclass

from amphora_contracts_representations import RetrievalRecord

from ..context.policy import require
from .identity import binding, binding_key, canonical, fingerprint, policy
from .selection import RetrievalSelection


@dataclass(frozen=True)
class RetrievalObservation:
    selection: RetrievalSelection
    canonical: bytes

    @classmethod
    def bind(cls, selection, supplied):
        selection = RetrievalSelection.bind(selection.request, selection.document(), selection.result_sha256)
        require(type(supplied) is RetrievalRecord, "retrieval_context_type")
        record = RetrievalRecord.model_validate(supplied.model_dump(mode="python", warnings=False))
        chosen, original = selection.document(), selection.request.document()
        scope = original.reference.scope
        require(record.actor_id == original.actor_id and record.retrieval_id == chosen.retrieval_id and
                record.generation == chosen.generation and record.query.reference == chosen.query,
                "retrieval_context_identity")
        query = binding(record.query, scope)
        normalized = policy(record.policy, scope)
        require(normalized == chosen.policy, "retrieval_context_policy")
        query_digest = fingerprint({"format": "data.retrieval-query.v1", "retrieval_id": record.retrieval_id,
            "actor_id": record.actor_id, "generation": record.generation.model_dump(mode="json"),
            "query": query.model_dump(mode="json"), "policy": normalized.model_dump(mode="json")})
        require(query_digest == record.query_sha256, "retrieval_context_query_digest")
        require(len(record.matches) <= normalized.top_k, "retrieval_context_top_k")
        seen, ordered, previous = set(), [], None
        for match in record.matches:
            member = binding(match.binding, scope)
            require(member.profile == query.profile, "retrieval_context_profile")
            require(normalized.bindings is None or member.reference in normalized.bindings, "retrieval_context_filter")
            require(member.reference.binding_id not in seen, "retrieval_context_duplicate_binding")
            seen.add(member.reference.binding_id)
            score = float(match.score) if match.score else 0.0
            key = (-score, *binding_key(member.reference))
            require(previous is None or previous < key, "retrieval_context_order")
            previous = key
            ordered.append({"binding": member.reference.model_dump(mode="json"), "score": score})
        result_digest = fingerprint({"format": "data.retrieval-result.v1", "query_sha256": query_digest, "matches": ordered})
        require(record.sha256 == result_digest == selection.result_sha256, "retrieval_context_result_digest")
        return cls(selection, canonical(record.model_dump(mode="json")))

    def document(self):
        return RetrievalRecord.model_validate_json(self.canonical)
