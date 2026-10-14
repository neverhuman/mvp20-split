import pytest

from amphora_contracts_search import RngInterval
from amphora_evolution_search.population import NumericBirth
from amphora_evolution_search.population.birth import birth_digest
from amphora_evolution_search.randomness import CounterRandom
from amphora_evolution_search.variation import ParentVector


def test_seed_waves_do_not_change_candidate_identity_or_rng(population_original):
    original = population_original
    expected = tuple(NumericBirth.seed(original, i).record for i in range(128))
    for batch in (1, 8, 32):
        actual = tuple(NumericBirth.seed(original, i).record for offset in range(0, 128, batch)
                       for i in range(offset, min(128, offset + batch)))
        assert actual == expected
    assert NumericBirth.seed(original, 999).record.draws.end == 1000
    assert len({r.candidate_id for r in expected}) == 128


def test_variation_reuses_exact_kernel_and_requires_original_parents(population_original):
    original = population_original
    seeds = tuple(NumericBirth.seed(original, i).record for i in range(2))
    parents = tuple(ParentVector(record.candidate_id, record.genes) for record in seeds)
    child = NumericBirth.vary(original, 1, 999, parents, CounterRandom(original.record.seed, 1000))
    assert child.record.draws == RngInterval(start=1000, end=1006)
    child.verify_parent_pool(parents)
    changed = tuple(ParentVector(parent.candidate_id, (0.0,)) for parent in parents)
    with pytest.raises(ValueError, match="birth_variation_replay"):
        child.verify_parent_pool(changed)


@pytest.mark.parametrize("case,code", [
    ("digest", "identity"), ("bounds", "bounds"), ("genes", "seed_replay"),
    ("draws", "seed_draws"), ("scope", "original"), ("reason", "proposed"),
    ("duplicate", "duplicate"), ("rejected", "rejected"),
])
def test_birth_negative_cases_even_with_recomputed_identity(population_original, case, code):
    original = population_original
    record = NumericBirth.seed(original, 0).record
    if case == "digest": record = record.model_copy(update={"candidate_id": "f" * 64})
    if case == "bounds": record = record.model_copy(update={"genes": (2.0,)})
    if case == "genes": record = record.model_copy(update={"genes": (0.0,)})
    if case == "draws": record = record.model_copy(update={"draws": RngInterval(start=1, end=2)})
    if case == "scope": record = record.model_copy(update={"scope": record.scope.model_copy(update={"project_id": "other"})})
    if case == "reason": record = record.model_copy(update={"reason_code": "invented"})
    if case == "duplicate": record = record.model_copy(update={"disposition": "duplicate", "reason_code": "duplicate_genes", "duplicate_of": record.candidate_id})
    if case == "rejected": record = record.model_copy(update={"disposition": "rejected"})
    if case != "digest": record = record.model_copy(update={"candidate_id": birth_digest(original, record)})
    with pytest.raises(ValueError, match="birth_" + code):
        NumericBirth(original, record)


def test_outcome_does_not_rewrite_birth_identity(population_original):
    birth = NumericBirth.seed(population_original, 0)
    rejected = birth.record.model_copy(update={"disposition": "rejected", "reason_code": "evaluation_budget"})
    assert NumericBirth(population_original, rejected).record.candidate_id == birth.record.candidate_id
