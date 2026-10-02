"""Pinned predicate/endpoint definitions; no domain-specific scientific inference."""

from dataclasses import dataclass

from amphora_contracts_knowledge import DomainVocabulary, VocabularyRef

from .canonical import KnowledgeError, digest


@dataclass(frozen=True)
class Vocabulary:
    record: DomainVocabulary

    def __post_init__(self):
        types = self.record.entity_types
        predicates = self.record.predicates
        if len(set(types)) != len(types) or len({p.predicate_id for p in predicates}) != len(predicates):
            raise KnowledgeError("duplicate_vocabulary_identity")
        for predicate in predicates:
            for allowed in (predicate.subject_types, predicate.object_types):
                if len(set(allowed)) != len(allowed) or not set(allowed).issubset(types):
                    raise KnowledgeError("invalid_predicate_endpoints")

    def canonical_record(self):
        predicates = tuple(predicate.model_copy(update={"subject_types": tuple(sorted(predicate.subject_types)),
            "object_types": tuple(sorted(predicate.object_types))})
            for predicate in sorted(self.record.predicates, key=lambda p: p.predicate_id))
        return self.record.model_copy(update={"entity_types": tuple(sorted(self.record.entity_types)),
                                              "predicates": predicates})

    @property
    def reference(self):
        return VocabularyRef(vocabulary_id=self.record.vocabulary_id, version=self.record.version,
                             sha256=digest(self.canonical_record()))

    def require_type(self, entity_type):
        if entity_type not in self.record.entity_types:
            raise KnowledgeError("unknown_entity_type")

    def require_relation(self, predicate_id, subject_type, object_type):
        predicate = next((p for p in self.record.predicates if p.predicate_id == predicate_id), None)
        if predicate is None:
            raise KnowledgeError("unknown_predicate")
        if subject_type not in predicate.subject_types or object_type not in predicate.object_types:
            raise KnowledgeError("predicate_endpoint_mismatch")
