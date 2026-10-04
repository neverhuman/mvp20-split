"""Validated immutable-snapshot membership and explicit historical status."""

import hashlib
from dataclasses import dataclass
from types import MappingProxyType

from amphora_contracts_knowledge import (
    DomainAssertion,
    DomainEntity,
    DomainGraphSnapshot,
    EntityRevisionRef,
    GraphAssertionDetail,
    GraphAssertionSummary,
    GraphEntityDetail,
    GraphEntitySummary,
)

from ..authoring.canonical import KnowledgeError, canonical
from ..authoring.references import ReferencedInputs


def require(condition, code):
    if not condition:
        raise KnowledgeError("explore_" + code)


def entity_key(ref):
    return ref.entity_id, ref.revision


def assertion_key(ref):
    return ref.assertion_id, ref.revision


@dataclass(frozen=True, slots=True)
class EntityStatus:
    record: DomainEntity
    is_latest: bool
    alias_target: EntityRevisionRef | None

    def summary(self):
        return GraphEntitySummary(
            reference=self.record.reference,
            entity_type=self.record.entity_type,
            label=self.record.label,
            is_latest=self.is_latest,
            alias_target=self.alias_target,
        )

    def detail(self):
        return GraphEntityDetail(
            kind="entity",
            record=self.record,
            is_latest=self.is_latest,
            alias_target=self.alias_target,
        )


@dataclass(frozen=True, slots=True)
class AssertionStatus:
    record: DomainAssertion
    is_latest: bool
    retracted: bool

    @property
    def active(self):
        return self.is_latest and not self.retracted

    def summary(self):
        r = self.record
        return GraphAssertionSummary(
            reference=r.reference,
            subject=r.subject,
            predicate=r.predicate,
            object=r.object,
            polarity=r.polarity,
            posture=r.posture,
            is_latest=self.is_latest,
            retracted=self.retracted,
        )

    def detail(self):
        return GraphAssertionDetail(
            kind="assertion",
            record=self.record,
            is_latest=self.is_latest,
            retracted=self.retracted,
        )


class EntityIndex:
    def __init__(self, content):
        records, latest, aliases = {}, {}, {}
        keys = [entity_key(r.reference) for r in content.entities]
        require(keys == sorted(keys) and len(keys) == len(set(keys)), "entity_order")
        for record in content.entities:
            ReferencedInputs.collect_records(content.graph, (record,))
            ref = record.reference
            prior = latest.get(ref.entity_id)
            require(
                record.supersedes == (None if prior is None else prior.reference),
                "entity_history",
            )
            require(
                ref.revision == (1 if prior is None else prior.reference.revision + 1),
                "entity_history",
            )
            if prior is not None:
                require(
                    (record.label, record.entity_type)
                    == (prior.label, prior.entity_type),
                    "entity_identity",
                )
            records[entity_key(ref)] = record
            latest[ref.entity_id] = record
        for alias in content.aliases:
            ReferencedInputs.collect_records(content.graph, (alias,))
            source, target = (
                records.get(entity_key(alias.source)),
                records.get(entity_key(alias.target)),
            )
            require(
                source is not None
                and source.reference == alias.source
                and target is not None
                and target.reference == alias.target,
                "alias_member",
            )
            require(
                source.entity_type == target.entity_type
                and source.reference != target.reference,
                "alias_identity",
            )
            require(
                alias.source.entity_id not in aliases
                and latest[alias.source.entity_id] == source,
                "alias_source",
            )
            aliases[alias.source.entity_id] = alias.target
        # Linear cycle detection, not repeated scans of long merge chains.
        completed = set()
        for start in aliases:
            visited, current = set(), start
            while current in aliases and current not in completed:
                require(current not in visited, "alias_cycle")
                visited.add(current)
                current = aliases[current].entity_id
            completed.update(visited)
        self.records = MappingProxyType(records)
        self.latest = MappingProxyType(latest)
        self.aliases = MappingProxyType(aliases)

    def get(self, reference):
        record = self.records.get(entity_key(reference))
        require(record is not None and record.reference == reference, "entity_missing")
        return EntityStatus(
            record,
            self.latest[reference.entity_id] == record,
            self.aliases.get(reference.entity_id),
        )

    def rows(self, history):
        rows = tuple(self.get(record.reference) for record in self.records.values())
        return (
            rows
            if history == "retained"
            else tuple(r for r in rows if r.is_latest and r.alias_target is None)
        )


class AssertionIndex:
    def __init__(self, content, entities):
        records, latest, retired = {}, {}, set()
        keys = [assertion_key(r.reference) for r in content.assertions]
        require(keys == sorted(keys) and len(keys) == len(set(keys)), "assertion_order")
        for record in content.assertions:
            ReferencedInputs.collect_records(content.graph, (record,))
            ref = record.reference
            prior = latest.get(ref.assertion_id)
            require(
                record.supersedes == (None if prior is None else prior.reference),
                "assertion_history",
            )
            require(
                ref.revision == (1 if prior is None else prior.reference.revision + 1),
                "assertion_history",
            )
            entities.get(record.subject)
            entities.get(record.object)
            records[assertion_key(ref)] = record
            latest[ref.assertion_id] = record
        for tombstone in content.retractions:
            ReferencedInputs.collect_records(content.graph, (tombstone,))
            ref = tombstone.assertion
            require(
                ref.assertion_id in latest
                and latest[ref.assertion_id].reference == ref,
                "retraction_member",
            )
            require(assertion_key(ref) not in retired, "duplicate_retraction")
            retired.add(assertion_key(ref))
        self.records = MappingProxyType(records)
        self.latest = MappingProxyType(latest)
        self.retired = frozenset(retired)

    def get(self, reference):
        record = self.records.get(assertion_key(reference))
        require(
            record is not None and record.reference == reference, "assertion_missing"
        )
        return AssertionStatus(
            record,
            self.latest[reference.assertion_id] == record,
            assertion_key(reference) in self.retired,
        )

    def rows(self, history):
        rows = tuple(self.get(record.reference) for record in self.records.values())
        return rows if history == "retained" else tuple(r for r in rows if r.active)


class SnapshotIndex:
    def __init__(self, snapshot):
        require(type(snapshot) is DomainGraphSnapshot, "snapshot_required")
        snapshot = DomainGraphSnapshot.model_validate_json(snapshot.model_dump_json())
        ref, content = snapshot.reference, snapshot.content
        raw = canonical(content)
        require(len(raw) <= 64 * 1024 * 1024, "snapshot_bound")
        require(
            ref.graph == content.graph
            and ref.revision == content.revision
            and ref.sha256 == hashlib.sha256(raw).hexdigest(),
            "snapshot_identity",
        )
        self.snapshot = snapshot
        self.entities = EntityIndex(content)
        self.assertions = AssertionIndex(content, self.entities)

    @property
    def reference(self):
        return self.snapshot.reference
