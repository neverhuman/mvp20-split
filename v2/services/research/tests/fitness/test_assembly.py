from dataclasses import replace
from decimal import Decimal, localcontext

import pytest
from amphora_research.fitness.assembly import FitnessAssembly
from amphora_research.fitness.policy import FitnessError, FitnessPolicy
from amphora_research.fitness.reuse import EvaluationKey
from amphora_research.observations.values import MissingValue, CensoredValue, CensorLimit, NumericValue, ReportedInterval

from .assembly_fixtures import assembly, inputs
from ..material_state.test_context import q
from ..observations.normalization.test_catalog import catalog


def test_optional_unknowns_do_not_veto_numeric_progress():
    result = assembly()
    assert result.disposition == 'ready' and result.synthesis_status == 'unknown'
    assert result.axes[0].amount == Decimal('1.25')
    assert {'accuracy', 'synthesis_unknown', 'controls_unknown'} <= set(result.focus)
    assert result.evidence.synthesis.assessment.alternatives[0].disposition == 'unknown'


@pytest.mark.parametrize('status,required,expected', [
    ('unknown',True,'unavailable'), ('failed',True,'excluded'), ('met',True,'ready'),
    ('unknown',False,'ready'), ('failed',False,'ready'),
])
def test_only_declared_synthesis_requirement_gates(status, required, expected):
    assert assembly(synthesis_status=status, synthesis_required=required).disposition == expected


@pytest.mark.parametrize('status,expected', [('supported','ready'), ('contradicted','excluded'), ('unknown','unavailable')])
def test_hard_eligibility_before_ranking(status, expected):
    result = assembly(eligibility_status=status)
    assert result.disposition == expected
    if expected != 'ready':
        with pytest.raises(FitnessError, match='requires_ready'):
            result.dominates(assembly())


@pytest.mark.parametrize('measurement,reason', [
    (MissingValue('unreported'), 'measurement_missing'),
    (CensoredValue(None,CensorLimit(q('2','mg/L'),True)), 'measurement_censored'),
])
def test_missing_and_censored_never_become_zero(measurement, reason):
    result = assembly(measurement=measurement)
    assert result.disposition == 'unavailable' and result.axes[0].amount is None
    assert reason in result.axes[0].reasons
    assert result.axes[0].values[0] == measurement


def test_uncertainty_and_original_values_survive_owner_normalization():
    original = NumericValue(q('1250','mg'), ReportedInterval(q('1000','mg'), q('1500','mg'), 'reported interval'))
    result = assembly(measurement=original, unit='g', normalization=catalog())
    assert result.disposition == 'ready' and result.axes[0].amount == Decimal('1.25')
    assert result.axes[0].values[0].uncertainty.lower.value.amount == Decimal('1')
    assert result.axes[0].reviews[0].observation.value.quantity.value == '1250'


def duplicates(second):
    def rows(plan, row):
        other = replace(row, identity=replace(row.identity, reference=replace(row.identity.reference, observation_id='second')),
                        value=NumericValue(q(second,'mg/L')))
        return row,other
    return rows


def test_replicates_require_exact_consensus_not_average_or_majority():
    assert assembly(rows=duplicates('1.2500')).disposition == 'ready'
    result = assembly(rows=duplicates('1.5'))
    assert result.disposition == 'unavailable'
    assert result.axes[0].reasons == ('conflicting_numeric_values',)
    assert len(result.axes[0].reviews) == 2
    assert assembly(rows=lambda plan,row:()).axes[0].reasons == ('missing_observation',)


def test_strict_observation_policy_remains_authoritative():
    result = assembly(strict=True)
    assert result.disposition == 'unavailable' and 'observation_unusable' in result.axes[0].reasons


def test_pareto_dominance_and_tie_are_exact_not_ambient_float_math():
    with localcontext() as context:
        context.prec = 2
        lower = assembly('1.234567890123456789')
        higher = assembly('1.234567890123456790')
        assert lower.dominates(higher) and not higher.dominates(lower)
        assert not lower.dominates(lower)


def test_policy_changes_cannot_silently_compare():
    with pytest.raises(FitnessError, match='context_mismatch'):
        assembly().dominates(assembly(synthesis_required=True, synthesis_status='met'))
    policy,key,evidence = inputs()
    with pytest.raises(FitnessError, match='reference_mismatch'):
        replace(policy,synthesis_required=True)
    assert policy.bytes


@pytest.mark.parametrize('field', ['eligibility', 'synthesis', 'interpretation', 'candidate'])
def test_foreign_owner_record_scopes_reject(field):
    policy,key,evidence = inputs()
    record = getattr(evidence,field)
    reference = record.reference.model_copy(update={'scope':record.reference.scope.model_copy(update={'project_id':'foreign'})})
    with pytest.raises(FitnessError, match='scope_mismatch'):
        FitnessAssembly.prepare(policy,key,replace(evidence,**{field:record.model_copy(update={'reference':reference})}))


def test_changed_representation_or_policy_rejects():
    policy,key,evidence = inputs()
    candidate = evidence.candidate.model_copy(update={'representation':evidence.candidate.representation.model_copy(update={'sha256':'e'*64})})
    with pytest.raises(FitnessError, match='representation_mismatch'):
        FitnessAssembly.prepare(policy,key,replace(evidence,candidate=candidate))
    changed = FitnessPolicy.prepare(policy.evaluation,policy.observation_use,True)
    with pytest.raises(FitnessError, match='evaluation_policy_mismatch'):
        FitnessAssembly.prepare(changed,key,evidence)


def test_multiobjective_tradeoffs_ties_and_both_directions():
    from ..observations.test_matching import observation
    def two_axes(plan):
        first = plan.expectations[0]
        second = replace(first,expectation_id='second',readout=replace(first.readout,criterion_id='yield'))
        return replace(plan,expectations=(first,second))
    def vector(first,second):
        def rows(plan,row):
            result = []
            for index,(expected,value) in enumerate(zip(plan.expectations,(first,second),strict=True)):
                item = observation(replace(plan,expectations=(expected,)),NumericValue(q(value,'mg/L')))
                result.append(replace(item,identity=replace(item.identity,reference=replace(item.identity.reference,observation_id='point-'+str(index)))))
            return tuple(result)
        return assembly(plan_transform=two_axes,rows=rows,directions={'yield':'maximize'})
    best,dominated,tradeoff,tied = vector('1','5'),vector('2','4'),vector('0','3'),vector('1.0','5.00')
    assert best.dominates(dominated)
    assert not dominated.dominates(best)
    assert not best.dominates(tradeoff) and not tradeoff.dominates(best)
    assert not best.dominates(tied) and not tied.dominates(best)


def test_missing_candidate_expectation_and_readout_mismatch_are_unavailable():
    policy,key,evidence = inputs()
    plan = evidence.interpretation.experiment
    expected = plan.expectations[0]
    for readout,reason in [
        (expected.readout.model_copy(update={'criterion_id':'foreign'}),'missing_expectation'),
        (expected.readout.model_copy(update={'unit':'g'}),'readout_incompatible'),
    ]:
        changed = plan.model_copy(update={'expectations':(expected.model_copy(update={'readout':readout}),)})
        result = FitnessAssembly.prepare(policy,key,replace(evidence,interpretation=evidence.interpretation.model_copy(update={'experiment':changed})))
        assert result.disposition == 'unavailable' and reason in result.axes[0].reasons


def test_wrong_specimen_and_incompatible_units_cannot_supply_fitness():
    policy,key,evidence = inputs()
    row = evidence.interpretation.reviews[0]
    binding = row.observation.binding
    changed = row.observation.model_copy(update={'binding':binding.model_copy(update={'role':'blank'})})
    interpreted = evidence.interpretation.model_copy(update={'reviews':(row.model_copy(update={'observation':changed}),)})
    result = FitnessAssembly.prepare(policy,key,replace(evidence,interpretation=interpreted))
    assert result.disposition == 'unavailable' and 'observation_binding_mismatch' in result.axes[0].reasons
    result = assembly(measurement=NumericValue(q('1','foreign-unit')))
    assert result.disposition == 'unavailable' and 'measurement_unit_mismatch' in result.axes[0].reasons


def test_unresolved_normalization_does_not_fall_back_to_numeric_original():
    policy,key,evidence = inputs(measurement=NumericValue(q('2','foreign-unit')),unit='g',normalization=catalog())
    result = FitnessAssembly.prepare(policy,key,evidence)
    assert result.disposition == 'unavailable' and 'normalization_unresolved' in result.axes[0].reasons
