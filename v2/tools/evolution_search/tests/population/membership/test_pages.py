import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import (
    CandidateMember, GenerationIdentity, MembershipManifest, MembershipPageReference,
    PopulationSpecification, membership_page_schema,
)
from amphora_evolution_search.population import GenerationMembership, OriginalPopulation, canonical

SPEC = Path(__file__).parents[1] / "specification/fixtures/specification.json"


def population(size=1000, *, long_scope=False):
    document = json.loads(SPEC.read_bytes())
    if long_scope:
        def widen(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"tenant_id", "project_id", "schema_id"}: value[key] = child.ljust(128, "x")
                    else: widen(child)
            elif isinstance(value, list):
                for child in value: widen(child)
        widen(document)
    original = OriginalPopulation(PopulationSpecification.model_validate_json(json.dumps(document)))
    identity = GenerationIdentity(scope=original.record.scope, run_id="population-run",
        specification_sha256=original.digest, generation=0, predecessor=None)
    def reference(index, kind):
        return ArtifactRef(artifact_id=f"{kind}-{index}", scope=identity.scope, sha256="a" * 64,
            media_type="application/json", schema_ref=original.record.representation, size_bytes=2)
    members = tuple(CandidateMember(candidate_id=f"{i:064x}", birth=reference(i, "birth"),
        representation=reference(i, "representation"), source="seed") for i in range(size))
    return GenerationMembership(original, identity, "cohort", members)


def published(value):
    pages = value.pages()
    payloads = tuple(canonical(page) for page in pages)
    references = tuple(MembershipPageReference(ordinal=i, members=len(page.members),
        artifact=ArtifactRef(artifact_id=f"page-{i}", scope=value.identity.scope,
            sha256=hashlib.sha256(raw).hexdigest(), media_type="application/json",
            schema_ref=membership_page_schema(), size_bytes=len(raw)))
        for i, (page, raw) in enumerate(zip(pages, payloads, strict=True)))
    manifest = MembershipManifest(schema_version="1", profile="population-membership-manifest-v1",
        generation=value.identity, role=value.role, member_count=len(value.members), pages=references)
    return canonical(manifest), payloads


@pytest.mark.parametrize("size", [0, 1, 64, 65, 128, 1000])
def test_canonical_closure_roundtrip(size):
    value = population(size)
    raw, pages = published(value)
    assert GenerationMembership.verified(value.original, raw, pages) == value
    assert all(len(page) <= 131072 for page in pages)
    assert len(pages) == (size + 63) // 64


@pytest.mark.parametrize("case,code", [
    ("missing", "page_coverage"), ("reordered", "page_digest"),
    ("corrupt", "page_digest"), ("count", "manifest_count"),
    ("ordinal", "page_ordinal"), ("scope", "page_binding"),
    ("schema", "page_binding"), ("whitespace", "manifest_canonical"),
    ("generation", "page_identity"), ("duplicate", "page_duplicate"),
])
def test_manifest_cannot_authorize_wrong_or_partial_bytes(case, code):
    value = population(65)
    raw, pages = published(value)
    manifest = json.loads(raw)
    if case == "missing": pages = pages[:-1]
    if case == "reordered": pages = tuple(reversed(pages))
    if case == "corrupt": pages = (pages[0] + b" ", pages[1])
    if case == "count": manifest["member_count"] = 64
    if case == "ordinal": manifest["pages"][0]["ordinal"] = 1
    if case == "scope": manifest["pages"][0]["artifact"]["scope"]["project_id"] = "other"
    if case == "schema": manifest["pages"][0]["artifact"]["schema_ref"]["sha256"] = "f" * 64
    if case == "generation": manifest["generation"]["run_id"] = "different-run"
    if case == "duplicate": manifest["pages"][1]["artifact"]["artifact_id"] = "page-0"
    raw = canonical(MembershipManifest.model_validate_json(json.dumps(manifest)))
    if case == "whitespace": raw += b"\n"
    with pytest.raises(ValueError, match="membership_" + code):
        GenerationMembership.verified(value.original, raw, pages)


def test_forged_valid_hash_does_not_hide_wrong_row_identity():
    value = population(2)
    raw, pages = published(value)
    page = json.loads(pages[0]); page["members"][1]["candidate_id"] = page["members"][0]["candidate_id"]
    altered = json.dumps(page, sort_keys=True, separators=(",", ":")).encode()
    manifest = json.loads(raw)
    artifact = manifest["pages"][0]["artifact"]
    artifact["sha256"] = hashlib.sha256(altered).hexdigest(); artifact["size_bytes"] = len(altered)
    with pytest.raises(ValueError, match="membership_order_or_duplicate"):
        GenerationMembership.verified(value.original, canonical(MembershipManifest.model_validate_json(json.dumps(manifest))), (altered,))


def test_wrong_predecessor_or_scope_never_establishes_generation_membership():
    value = population(1)
    for change, code in [({"generation": 1}, "predecessor"),
                         ({"specification_sha256": "f" * 64}, "original_binding")]:
        with pytest.raises(ValueError, match="membership_" + code):
            GenerationMembership(value.original, value.identity.model_copy(update=change), value.role, value.members)


def test_page_byte_bound_can_split_before_member_bound():
    value = population(100, long_scope=True)
    # Core ArtifactRef permits UTF-8 media labels: use a wire-only placeholder
    # to distinguish encoded bytes from character count, not a MIME registration claim.
    def long(reference):
        return reference.model_copy(update={"artifact_id": reference.artifact_id.ljust(128, "x"),
            "media_type": "application/" + "\u00e9" * 116})
    members = tuple(member.model_copy(update={"birth": long(member.birth), "representation": long(member.representation)})
                    for member in value.members)
    expanded = GenerationMembership(value.original, value.identity, value.role, members)
    # Byte pressure also includes long schema and scope fields, kept compatible.
    assert len(expanded.pages()[0].members) < 64
    assert all(len(canonical(page)) <= 131072 for page in expanded.pages())
    assert GenerationMembership.verified(expanded.original, *published(expanded)) == expanded
