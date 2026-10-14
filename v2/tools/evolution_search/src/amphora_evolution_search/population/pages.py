"""Bounded deterministic page packing/byte verification for population records."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_population import (
    BirthPage, EvaluationKeyPage, FitnessPage, GenerationIdentity, MethodObservationPage, MembershipPageReference,
    SelectionPage, population_record_schema,
)

from ..ranking import require
from .membership import CLOSURE_BYTES, PAGE_BYTES, ROW_BYTES
from .specification import canonical


def key_digest(record):
    return hashlib.sha256(b"amphora.population/evaluation-v1\0" + canonical(record)).hexdigest()


_KINDS = {
    "population.birth-page": (BirthPage, "records", "population-birth-page-v1", 1000,
                              lambda row: (row.generation, row.ordinal, row.candidate_id)),
    "population.evaluation-key-page": (EvaluationKeyPage, "records", "population-evaluation-key-page-v1", 16000, key_digest),
    "population.method-observation-page": (MethodObservationPage, "records", "population-method-observation-page-v1", 16000,
                                           lambda row: row.evaluation_sha256),
    "population.fitness-page": (FitnessPage, "records", "population-fitness-page-v1", 2000, lambda row: row.candidate_id),
    "population.selection-page": (SelectionPage, "members", "population-selection-page-v1", 2000, lambda row: row.candidate_id),
}


@dataclass(frozen=True)
class RecordPages:
    generation: GenerationIdentity
    schema_name: str
    records: tuple

    def __post_init__(self):
        identity = GenerationIdentity.model_validate_json(self.generation.model_dump_json())
        object.__setattr__(self, "generation", identity)
        require(self.schema_name in _KINDS, "record_page_kind")
        model, field, profile, maximum, ordering = _KINDS[self.schema_name]
        require(type(self.records) is tuple and len(self.records) <= maximum, "record_page_count")
        checked, total_bytes = [], 0
        for row in self.records:
            page = model.model_validate_json(json.dumps({"schema_version": "1", "profile": profile,
                "generation": identity.model_dump(mode="json"), "ordinal": 0, field: [row.model_dump(mode="json")]}))
            row = getattr(page, field)[0]
            require(len(canonical(row)) <= ROW_BYTES, "record_row_bytes")
            total_bytes += len(canonical(row))
            require(total_bytes <= CLOSURE_BYTES, "record_closure_bytes")
            if self.schema_name == "population.birth-page":
                require(row.scope == identity.scope and row.specification_sha256 == identity.specification_sha256
                        and row.generation == identity.generation, "record_generation")
            elif self.schema_name != "population.selection-page":
                source = row.key.generation if self.schema_name == "population.method-observation-page" else row.generation
                if self.schema_name == "population.fitness-page":
                    require(source.scope == identity.scope and source.run_id == identity.run_id
                            and source.specification_sha256 == identity.specification_sha256
                            and source.generation <= identity.generation, "record_generation")
                else:
                    require(source == identity, "record_generation")
            checked.append(row)
        object.__setattr__(self, "records", tuple(checked))
        keys = tuple(ordering(row) for row in checked)
        require(keys == tuple(sorted(set(keys))), "record_order_or_duplicate")
        if self.schema_name == "population.birth-page":
            require(len({row.ordinal for row in checked}) == len(checked), "record_birth_ordinal_duplicate")

    def pack(self):
        model, field, profile, _, _ = _KINDS[self.schema_name]
        pages, pending = [], []
        def page(rows):
            return model(schema_version="1", profile=profile, generation=self.generation,
                         ordinal=len(pages), **{field: tuple(rows)})
        for row in self.records:
            next_page = page([*pending, row]) if len(pending) < 64 else None
            if next_page is None or len(canonical(next_page)) > PAGE_BYTES:
                require(bool(pending), "record_page_bytes")
                pages.append(page(pending)); pending = []
            pending.append(row)
            require(len(canonical(page(pending))) <= PAGE_BYTES, "record_page_bytes")
        if pending: pages.append(page(pending))
        require(len(pages) <= 512 and sum(len(canonical(p)) for p in pages) <= CLOSURE_BYTES, "record_closure_bytes")
        return tuple(pages)

    @classmethod
    def verified(cls, generation, schema_name, references, payloads, count):
        require(schema_name in _KINDS, "record_page_kind")
        require(type(references) is tuple and type(payloads) is tuple and len(references) == len(payloads) <= 512,
                "record_page_coverage")
        generation = GenerationIdentity.model_validate_json(generation.model_dump_json())
        references = tuple(MembershipPageReference.model_validate_json(r.model_dump_json()) for r in references)
        require(type(count) is int and 0 <= count <= _KINDS[schema_name][3], "record_page_count")
        model, field, _, _, _ = _KINDS[schema_name]
        records, seen, total = [], set(), 0
        for ordinal, (reference, raw) in enumerate(zip(references, payloads, strict=True)):
            artifact = reference.artifact
            require(type(raw) is bytes and len(raw) <= PAGE_BYTES, "record_page_bytes")
            total += len(raw)
            require(total <= CLOSURE_BYTES, "record_closure_bytes")
            require(reference.ordinal == ordinal and artifact.artifact_id not in seen, "record_page_position")
            seen.add(artifact.artifact_id)
            require(artifact.scope == generation.scope and artifact.schema_ref == population_record_schema(schema_name)
                    and artifact.media_type == "application/json", "record_page_binding")
            require(artifact.size_bytes == len(raw) and artifact.sha256 == hashlib.sha256(raw).hexdigest(), "record_page_digest")
            page = model.model_validate_json(raw)
            require(canonical(page) == raw and page.ordinal == ordinal and page.generation == generation, "record_page_identity")
            require(reference.members == len(getattr(page, field)), "record_page_members")
            records.extend(getattr(page, field))
        require(len(records) == count, "record_total_count")
        result = cls(generation, schema_name, tuple(records))
        require(tuple(canonical(page) for page in result.pack()) == payloads, "record_page_partition")
        return result
