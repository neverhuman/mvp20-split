"""Deterministic bounded membership closure; pure bytes, never Data authority."""

import hashlib
from dataclasses import dataclass
from functools import cached_property
from types import MappingProxyType

from amphora_contracts_population import (
    CandidateMember, GenerationIdentity, MembershipManifest, MembershipPage, membership_page_schema,
    candidate_birth_schema, population_record_schema,
)

from ..ranking import require
from .specification import OriginalPopulation, canonical

ROW_BYTES = 8192
PAGE_BYTES = 131072
MANIFEST_BYTES = 262144
CLOSURE_BYTES = 67108864


@dataclass(frozen=True)
class GenerationMembership:
    original: OriginalPopulation
    identity: GenerationIdentity
    role: str
    members: tuple[CandidateMember, ...]

    def __post_init__(self):
        identity = GenerationIdentity.model_validate_json(self.identity.model_dump_json())
        object.__setattr__(self, "identity", identity)
        require(identity.scope == self.original.record.scope and identity.specification_sha256 == self.original.digest,
                "membership_original_binding")
        require(identity.generation <= self.original.record.budget.successor_generations, "membership_generation_budget")
        require((identity.predecessor is None) == (identity.generation == 0), "membership_predecessor")
        if identity.predecessor is not None:
            require(identity.predecessor.scope == identity.scope, "membership_predecessor_scope")
            require(identity.predecessor.schema_ref == population_record_schema("population.checkpoint")
                    and identity.predecessor.media_type == "application/json", "membership_predecessor_schema")
        require(self.role in {"cohort", "selection_pool"}, "membership_role")
        require(type(self.members) is tuple, "membership_tuple")
        maximum = self.original.record.budget.population_size * (2 if self.role == "selection_pool" else 1)
        require(len(self.members) <= maximum, "membership_count")
        checked = tuple(CandidateMember.model_validate_json(member.model_dump_json()) for member in self.members)
        object.__setattr__(self, "members", checked)
        identifiers = tuple(member.candidate_id for member in checked)
        require(identifiers == tuple(sorted(set(identifiers))), "membership_order_or_duplicate")
        references = {}
        for member in checked:
            require(len(canonical(member)) <= ROW_BYTES, "membership_row_bytes")
            require(member.birth.scope == member.representation.scope == identity.scope, "membership_member_scope")
            require(member.birth.schema_ref == candidate_birth_schema() and member.birth.media_type == "application/json",
                    "membership_birth_schema")
            require(member.representation.schema_ref == self.original.record.representation, "membership_representation")
            require((member.source == "seed") == (identity.generation == 0), "membership_source_generation")
            for reference in (member.birth, member.representation):
                require(references.setdefault(reference.artifact_id, reference) == reference, "membership_artifact_conflict")

    @cached_property
    def by_id(self):
        return MappingProxyType({member.candidate_id: member for member in self.members})

    def pages(self):
        """Pack canonical order by both byte and member limits, independent of dispatch."""
        pages, pending = [], []
        def record(members):
            return MembershipPage(schema_version="1", profile="population-membership-v1", generation=self.identity,
                                  role=self.role, ordinal=len(pages), members=tuple(members))
        for member in self.members:
            candidate = record([*pending, member]) if len(pending) < 64 else None
            if candidate is None or len(canonical(candidate)) > PAGE_BYTES:
                require(bool(pending), "membership_page_bytes")
                pages.append(record(pending))
                pending = []
            pending.append(member)
            require(len(canonical(record(pending))) <= PAGE_BYTES, "membership_page_bytes")
        if pending:
            pages.append(record(pending))
        require(len(pages) <= 512 and sum(len(canonical(p)) for p in pages) <= CLOSURE_BYTES, "membership_closure_bytes")
        return tuple(pages)

    @classmethod
    def verified(cls, original, manifest, payloads):
        """Verify supplied manifest/page bytes; caller still owns access and retention."""
        require(type(manifest) is bytes and len(manifest) <= MANIFEST_BYTES, "membership_manifest_bytes")
        root = MembershipManifest.model_validate_json(manifest)
        require(canonical(root) == manifest, "membership_manifest_canonical")
        require(type(payloads) is tuple and len(payloads) == len(root.pages), "membership_page_coverage")
        total, members = 0, []
        seen = set()
        for ordinal, (reference, raw) in enumerate(zip(root.pages, payloads, strict=True)):
            require(reference.ordinal == ordinal, "membership_page_ordinal")
            artifact = reference.artifact
            require(artifact.artifact_id not in seen, "membership_page_duplicate")
            seen.add(artifact.artifact_id)
            require(type(raw) is bytes and len(raw) <= PAGE_BYTES, "membership_page_bytes")
            total += len(raw)
            require(total <= CLOSURE_BYTES, "membership_closure_bytes")
            require(artifact.scope == root.generation.scope and artifact.schema_ref == membership_page_schema()
                    and artifact.media_type == "application/json", "membership_page_binding")
            require(artifact.size_bytes == len(raw) and artifact.sha256 == hashlib.sha256(raw).hexdigest(),
                    "membership_page_digest")
            page = MembershipPage.model_validate_json(raw)
            require(canonical(page) == raw, "membership_page_canonical")
            require(page.generation == root.generation and page.role == root.role and page.ordinal == ordinal,
                    "membership_page_identity")
            require(reference.members == len(page.members), "membership_page_count")
            members.extend(page.members)
        require(root.member_count == len(members), "membership_manifest_count")
        result = cls(original, root.generation, root.role, tuple(members))
        # A producer cannot alter page partitioning while claiming the canonical profile.
        require(tuple(canonical(page) for page in result.pages()) == payloads, "membership_page_partition")
        return result
