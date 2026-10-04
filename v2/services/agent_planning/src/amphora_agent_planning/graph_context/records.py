"""Shared pure graph record invariants; no task-specific schema or owner I/O."""

import hashlib
import json
import unicodedata
from dataclasses import dataclass

from amphora_contracts_knowledge import DomainGraphSnapshot, GraphAuthoringProfile

from ..context.policy import require


def canonical(record):
    return json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def label_key(label):
    # Case is meaningful in scientific identifiers (Co and CO, for example).
    return unicodedata.normalize("NFC", label).strip()


@dataclass(frozen=True)
class PinnedGraphContext:
    profile_bytes: bytes
    snapshot_bytes: bytes | None

    @classmethod
    def bind(cls, pins, profile, snapshot):
        target = pins.validated()
        profile = GraphAuthoringProfile.model_validate(profile.model_dump(mode="python", warnings=False))
        require(profile.graph == target.graph and profile.vocabulary_reference == target.vocabulary and
                profile.policy == target.policy, "graph_profile_binding")
        vocabulary = profile.vocabulary
        require(len(set(vocabulary.entity_types)) == len(vocabulary.entity_types) and
                len({p.predicate_id for p in vocabulary.predicates}) == len(vocabulary.predicates),
                "graph_vocabulary_duplicate")
        predicates = []
        for predicate in sorted(vocabulary.predicates, key=lambda item: item.predicate_id):
            for types in (predicate.subject_types, predicate.object_types):
                require(len(set(types)) == len(types) and set(types).issubset(vocabulary.entity_types),
                        "graph_vocabulary_endpoints")
            predicates.append(predicate.model_copy(update={"subject_types": tuple(sorted(predicate.subject_types)),
                                                            "object_types": tuple(sorted(predicate.object_types))}))
        normalized = vocabulary.model_copy(update={"entity_types": tuple(sorted(vocabulary.entity_types)),
                                                   "predicates": tuple(predicates)})
        ref = profile.vocabulary_reference
        require(ref.vocabulary_id == vocabulary.vocabulary_id and ref.version == vocabulary.version and
                ref.sha256 == hashlib.sha256(canonical(normalized)).hexdigest(), "graph_vocabulary_digest")
        profile = profile.model_copy(update={"vocabulary": normalized})
        profile_bytes = canonical(profile)
        require(len(profile_bytes) <= 262144, "graph_profile_size")
        if target.base is None:
            require(snapshot is None, "graph_genesis_binding")
            return cls(profile_bytes, None)
        require(snapshot is not None, "graph_snapshot_missing")
        snapshot = DomainGraphSnapshot.model_validate(snapshot.model_dump(mode="python", warnings=False))
        content = snapshot.content
        require(snapshot.reference == target.base.snapshot and content.graph == target.graph and
                content.revision == snapshot.reference.revision == target.base.change.position and
                target.base.change.graph == target.graph and content.vocabulary == target.vocabulary and
                content.policy == target.policy, "graph_snapshot_binding")
        require(hashlib.sha256(canonical(content)).hexdigest() == snapshot.reference.sha256, "graph_snapshot_digest")
        encoded = canonical(snapshot)
        require(len(encoded) <= 16 * 1024 * 1024, "graph_snapshot_size")
        result = cls(profile_bytes, encoded)
        result.index()  # Reject malformed owner records before deriving lookup facts.
        return result

    def profile(self):
        return GraphAuthoringProfile.model_validate_json(self.profile_bytes)

    def snapshot(self):
        return None if self.snapshot_bytes is None else DomainGraphSnapshot.model_validate_json(self.snapshot_bytes)

    def index(self):
        snapshot = self.snapshot()
        graph = self.profile().graph
        entities, assertions, aliases, retracted = {}, {}, {}, set()
        if snapshot is not None:
            for records, index in ((snapshot.content.entities, entities), (snapshot.content.assertions, assertions)):
                for record in records:
                    ref = record.reference
                    require(ref.graph == graph and ref not in index, "graph_record_identity")
                    index[ref] = record
            for alias in snapshot.content.aliases:
                require(alias.source in entities and alias.target in entities and
                        alias.source.entity_id not in aliases, "graph_alias_identity")
                aliases[alias.source.entity_id] = alias.target
            for row in snapshot.content.retractions:
                require(row.assertion in assertions and row.assertion not in retracted, "graph_retraction_identity")
                retracted.add(row.assertion)
            for record in assertions.values():
                require(record.subject in entities and record.object in entities, "graph_assertion_endpoints")
        result = GraphFacts(entities, assertions, aliases, frozenset(retracted))
        for ref in entities:
            result.resolve(ref)
        return result


@dataclass(frozen=True)
class GraphFacts:
    entities: dict
    assertions: dict
    aliases: dict
    retracted: frozenset

    def resolve(self, reference):
        require(reference in self.entities, "unknown_entity_revision")
        seen = set()
        while reference.entity_id in self.aliases:
            require(reference.entity_id not in seen, "graph_alias_cycle")
            seen.add(reference.entity_id)
            reference = self.aliases[reference.entity_id]
        return reference

    def entity(self, reference, *, editable=False):
        require(reference in self.entities, "unknown_entity_revision")
        require(not any(ref.entity_id == reference.entity_id and ref.revision > reference.revision
                        for ref in self.entities), "stale_entity_revision")
        require(not editable or reference.entity_id not in self.aliases, "entity_already_merged")
        return self.entities[reference]

    def assertion(self, reference):
        require(reference in self.assertions, "unknown_assertion_revision")
        require(not any(ref.assertion_id == reference.assertion_id and ref.revision > reference.revision
                        for ref in self.assertions), "stale_assertion_revision")
        require(reference not in self.retracted, "assertion_retracted")
        return self.assertions[reference]

    def labels(self, label, entity_type):
        latest = {}
        for ref, record in self.entities.items():
            if ref.entity_id not in latest or ref.revision > latest[ref.entity_id].reference.revision:
                latest[ref.entity_id] = record
        return tuple(record for record in latest.values() if record.entity_type == entity_type and
                     label_key(record.label) == label_key(label))
