import pytest

from amphora_contracts_population import UnavailableMethod, UnavailablePopulationFitness
from amphora_evolution_search.population import FitnessEvidence, GenerationMembership, PopulationSelection


def test_zero_and_weak_present_evidence_remain_scores(assessment_factory):
    evidence, factory = assessment_factory
    result = evidence.bind(factory(value=0.0, confidence=0.0))
    assert result.score.objectives == (0.0,) and result.score.eligible


def test_missing_required_method_cannot_be_scored(assessment_factory):
    evidence, factory = assessment_factory
    observations = list(evidence.observations)
    candidate = factory().candidate_id
    index = next(i for i, row in enumerate(observations) if row.key.candidate_id == candidate)
    observations[index] = observations[index].model_copy(update={"outcome": UnavailableMethod(
        status="failed", reason_code="tool_failed", producer=None, evidence=())})
    failed = FitnessEvidence(evidence.evaluations, tuple(observations))
    with pytest.raises(ValueError, match="fitness_required_unavailable"):
        failed.bind(factory())
    unavailable = factory().model_copy(update={"outcome": UnavailablePopulationFitness(status="unavailable", reason_code="tool_failed")})
    retained = failed.bind(unavailable)
    with pytest.raises(ValueError, match="fitness_not_available"): _ = retained.score


@pytest.mark.parametrize("case,code", [
    ("units", "objective_identity"), ("method", "objective_methods"),
    ("foreign", "evidence_unavailable"), ("duplicate", "evidence_duplicate"),
    ("cut", "evaluation_set"), ("policy", "assembly_policy"),
])
def test_fitness_binding_is_not_only_shape(assessment_factory, case, code):
    evidence, factory = assessment_factory; record = factory(); objective = record.outcome.objectives[0]
    if case == "units": objective = objective.model_copy(update={"value": objective.value.model_copy(update={"unit": "wrong"})})
    if case == "method": objective = objective.model_copy(update={"evaluations": objective.evaluations[:1]})
    if case == "foreign": objective = objective.model_copy(update={"evaluations": ("f" * 64,)})
    if case == "duplicate": objective = objective.model_copy(update={"evaluations": objective.evaluations * 2})
    record = record.model_copy(update={"outcome": record.outcome.model_copy(update={"objectives": (objective,)})})
    if case == "cut": record = record.model_copy(update={"evaluation_set_sha256": "f" * 64})
    if case == "policy": record = record.model_copy(update={"policy": record.policy.model_copy(update={"sha256": "f" * 64})})
    with pytest.raises(ValueError, match="fitness_" + code): evidence.bind(record)


def pool(evidence):
    cohort = evidence.evaluations.membership
    return GenerationMembership(cohort.original, cohort.identity, "selection_pool", cohort.members)


def test_selection_uses_whole_pool_and_stable_ranks(assessment_factory):
    evidence, factory = assessment_factory
    fitness = (evidence.bind(factory(0, 10.0)), evidence.bind(factory(1, 0.0)))
    decision = PopulationSelection(pool(evidence), fitness).decide()
    assert decision.selected[0] == fitness[1].record.candidate_id
    assert decision.disposition == "insufficient_survivors" and not decision.stopped
    assert decision == PopulationSelection(pool(evidence), tuple(reversed(fitness))).decide()
    assert sum(len(page.members) for page in decision.pages()) == 2
    with pytest.raises(ValueError, match="selection_fitness_coverage"):
        PopulationSelection(pool(evidence), fitness[:1])


def test_missing_fitness_excludes_without_fabricating_zero(assessment_factory):
    evidence, factory = assessment_factory
    absent = factory(1).model_copy(update={"outcome": UnavailablePopulationFitness(status="unavailable", reason_code="assembly_failed")})
    decision = PopulationSelection(pool(evidence), (evidence.bind(factory(0, 100.0)), evidence.bind(absent))).decide()
    assert decision.disposition == "insufficient_eligible_parents" and decision.stopped
    assert len(decision.selected) == 1
    assert sum(row.status == "excluded" for row in decision.members) == 1


def test_infeasible_is_ranked_but_never_selected(assessment_factory):
    evidence, factory = assessment_factory
    decision = PopulationSelection(pool(evidence), tuple(evidence.bind(factory(i, violation=1.0)) for i in range(2))).decide()
    assert decision.disposition == "no_feasible_survivors" and decision.stopped
    assert decision.selected == () and all(row.status == "ranked" and not row.feasible for row in decision.members)
