"""Aggregate page budget across families; callers still establish full manifest reachability."""

from dataclasses import dataclass

from amphora_contracts_population import (
    BirthPage, EvaluationKeyPage, EvaluationSlotPage, FitnessPage, MaterialMappingPage,
    MembershipPage, MethodObservationPage, SelectionPage, GenerationIdentity, membership_page_schema, population_record_schema,
)

from ..ranking import require
from .membership import CLOSURE_BYTES, PAGE_BYTES
from .specification import canonical
from .retained import PopulationArtifact


_PAGES = {
    "population.membership-page": MembershipPage,
    "population.birth-page": BirthPage,
    "population.evaluation-key-page": EvaluationKeyPage,
    "population.evaluation-slot-page": EvaluationSlotPage,
    "population.method-observation-page": MethodObservationPage,
    "population.fitness-page": FitnessPage,
    "population.selection-page": SelectionPage,
    "population.material-mapping-page": MaterialMappingPage,
}


@dataclass(frozen=True)
class GenerationPageClosure:
    generation: GenerationIdentity
    pages: tuple[PopulationArtifact, ...]
    size_bytes: int

    @classmethod
    def verify(cls, generation, pages):
        generation = GenerationIdentity.model_validate_json(generation.model_dump_json())
        require(type(pages) is tuple and len(pages) <= 512, "generation_closure_pages")
        require(len({p.reference.artifact_id for p in pages}) == len(pages), "generation_closure_duplicate")
        require(all(type(p.content) is bytes and len(p.content) <= PAGE_BYTES for p in pages), "generation_closure_page_bytes")
        size = sum(len(p.content) for p in pages)
        require(size <= CLOSURE_BYTES, "generation_closure_bytes")
        for artifact in pages:
            name = artifact.reference.schema_ref.schema_id
            require(name in _PAGES, "generation_closure_page_schema")
            schema = membership_page_schema() if name == "population.membership-page" else population_record_schema(name)
            page = artifact.decode(_PAGES[name], schema, generation.scope)
            identity = page.context.generation if name == "population.material-mapping-page" else page.generation
            require(identity.scope == generation.scope and identity.run_id == generation.run_id
                    and identity.specification_sha256 == generation.specification_sha256
                    and identity.generation <= generation.generation
                    and (identity.generation < generation.generation or identity == generation), "generation_closure_identity")
            rows = (*page.pairs, *page.excluded) if name == "population.material-mapping-page" else page.members if name in {
                "population.membership-page", "population.selection-page"} else page.records
            require(1 <= len(rows) <= 64 and all(len(canonical(row)) <= 8192 for row in rows), "generation_closure_rows")
        return cls(generation, pages, size)
