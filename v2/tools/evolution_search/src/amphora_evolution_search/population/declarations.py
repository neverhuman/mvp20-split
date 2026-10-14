"""Declared work coverage is independent of input availability and attempt identity."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_population import (EvaluationDeclarationManifest, EvaluationResolutionManifest, EvaluationSlot,
                                          membership_manifest_schema, population_record_schema)

from ..ranking import require
from .evaluations import FrozenEvaluations
from .membership import GenerationMembership
from .pages import RecordPages
from .specification import canonical


def slot_address(record):
    return record.candidate_id, record.method_id, record.occurrence_id


def slot_digest(record):
    return hashlib.sha256(b"amphora.population/evaluation-slot-v1\0" + canonical(record)).hexdigest()


@dataclass(frozen=True)
class DeclaredEvaluations:
    membership: GenerationMembership
    slots: tuple[EvaluationSlot, ...]

    def __post_init__(self):
        require(self.membership.role == "cohort", "declaration_cohort")
        require(type(self.slots) is tuple and len(self.slots) <= 8000, "declaration_count")
        slots = tuple(EvaluationSlot.model_validate_json(slot.model_dump_json()) for slot in self.slots)
        members = {m.candidate_id for m in self.membership.members}
        methods = {m.method_id: m for m in self.membership.original.record.method_graph.methods}
        for slot in slots:
            require(len(canonical(slot)) <= 8192 and slot.generation == self.membership.identity, "declaration_generation")
            require(slot.candidate_id in members and slot.method_id in methods, "declaration_method_member")
        addresses = {slot_address(slot) for slot in slots}
        require(len(addresses) == len(slots), "declaration_duplicate")
        covered = {(slot.candidate_id, slot.method_id) for slot in slots}
        require(all((member, method.method_id) in covered for member in members for method in methods.values() if method.required),
                "declaration_required_coverage")
        object.__setattr__(self, "slots", tuple(sorted(slots, key=slot_digest)))

    @classmethod
    def primary(cls, membership):
        """Explicit one-occurrence-per-method fixture policy; not inferred topology."""
        return cls(membership, tuple(EvaluationSlot(schema_version="1", profile="population-evaluation-slot-v1",
            generation=membership.identity, candidate_id=member.candidate_id, method_id=method.method_id, occurrence_id="primary")
            for member in membership.members for method in membership.original.record.method_graph.methods))

    @property
    def digest(self):
        payload = {"generation": self.membership.identity.model_dump(mode="json"),
                   "members": [m.candidate_id for m in self.membership.members],
                   "slots": [slot_digest(slot) for slot in self.slots]}
        return hashlib.sha256(b"amphora.population/evaluation-slot-set-v1\0" + json.dumps(payload, sort_keys=True,
            separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()

    def resolve(self, keys):
        frozen = FrozenEvaluations(self.membership, keys)
        require({slot_address(key.record) for key in frozen.keys} == {slot_address(slot) for slot in self.slots},
                "declaration_resolution_coverage")
        return frozen

    @classmethod
    def verified(cls, membership, membership_reference, artifact, payloads):
        require(membership_reference.scope == membership.identity.scope
                and membership_reference.schema_ref == membership_manifest_schema(), "declaration_membership_reference")
        root = artifact.decode(EvaluationDeclarationManifest, population_record_schema("population.evaluation-declarations"), membership.identity.scope)
        require(root.generation == membership.identity and root.membership == membership_reference, "declaration_manifest_source")
        rows = RecordPages.verified(root.generation, "population.evaluation-slot-page", root.pages, payloads, root.slot_count)
        result = cls(membership, rows.records)
        require(root.slot_set_sha256 == result.digest, "declaration_manifest_digest")
        return result

    def verify_resolution(self, declaration_artifact, evaluation_artifact, record, frozen):
        checked = EvaluationResolutionManifest.model_validate_json(record.model_dump_json())
        require(len(canonical(checked)) <= 262144, "resolution_manifest_bytes")
        require(declaration_artifact.scope == evaluation_artifact.scope == self.membership.identity.scope
                and declaration_artifact.schema_ref == population_record_schema("population.evaluation-declarations")
                and evaluation_artifact.schema_ref == population_record_schema("population.evaluation-manifest"), "resolution_source_schema")
        require(checked.generation == self.membership.identity and checked.declarations == declaration_artifact
                and checked.evaluations == evaluation_artifact and checked.slot_set_sha256 == self.digest, "resolution_source_binding")
        require(frozen.membership == self.membership and self.resolve(frozen.keys).digest == checked.evaluation_set_sha256,
                "resolution_key_set")
