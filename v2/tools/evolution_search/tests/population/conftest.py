import hashlib
from pathlib import Path

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import CandidateMember, GenerationIdentity, PopulationSpecification, candidate_birth_schema
from amphora_evolution_search.population import GenerationMembership, NumericBirth, OriginalPopulation, canonical


@pytest.fixture
def population_original():
    return OriginalPopulation(PopulationSpecification.model_validate_json(
        (Path(__file__).parent / "specification/fixtures/specification.json").read_bytes()))


@pytest.fixture
def born_cohort(population_original):
    original = population_original
    identity = GenerationIdentity(scope=original.record.scope, run_id="test-run", specification_sha256=original.digest,
                                  generation=0, predecessor=None)
    members = []
    for ordinal in range(2):
        birth = NumericBirth.seed(original, ordinal)
        reference = ArtifactRef(artifact_id=f"birth-{ordinal}", scope=identity.scope,
            sha256=hashlib.sha256(canonical(birth.record)).hexdigest(), media_type="application/json",
            schema_ref=candidate_birth_schema(), size_bytes=len(canonical(birth.record)))
        representation = reference.model_copy(update={"artifact_id": f"vector-{ordinal}", "schema_ref": original.record.representation})
        members.append(CandidateMember(candidate_id=birth.record.candidate_id, birth=reference,
                                       representation=representation, source="seed"))
    return GenerationMembership(original, identity, "cohort", tuple(sorted(members, key=lambda m: m.candidate_id)))
