"""Independent BP-08.03/B3 comparison and action-gate oracles."""
from dataclasses import replace

import pytest
from amphora_research.fitness.assembly import FitnessAssembly
from amphora_research.fitness.policy import FitnessError, FitnessPolicy
from amphora_research.fitness.reuse import EvaluationKey
from amphora_research.observations.values import NumericValue

from .assembly_fixtures import assembly, inputs
from ..material_state.test_context import q
from ..observations.test_matching import observation


def test_different_evaluator_releases_cannot_silently_compare_ready_values():
    policy,key,evidence=inputs()
    evaluator=policy.evaluation.method.evaluator.model_copy(update={'release':'99.0.0'})
    method=policy.evaluation.method.model_copy(update={'evaluator':evaluator})
    changed=FitnessPolicy.prepare(policy.evaluation.model_copy(update={'method':method}),policy.observation_use,policy.synthesis_required)
    other=FitnessAssembly.prepare(changed,EvaluationKey(key.record.model_copy(update={'policy':changed.evaluation})),evidence)
    original=FitnessAssembly.prepare(policy,key,evidence)
    assert original.disposition==other.disposition=='ready'
    with pytest.raises(FitnessError,match='comparison_context_mismatch'):original.dominates(other)


def test_different_objective_dimensions_never_zip_to_a_partial_comparison():
    def two_axes(plan):
        first=plan.expectations[0]
        second=replace(first,expectation_id='second',readout=replace(first.readout,criterion_id='second'))
        return replace(plan,expectations=(first,second))
    def rows(plan,_row):
        result=[]
        for index,expected in enumerate(plan.expectations):
            item=observation(replace(plan,expectations=(expected,)),NumericValue(q('1','mg/L')))
            result.append(replace(item,identity=replace(item.identity,reference=replace(item.identity.reference,observation_id='axis-'+str(index)))))
        return tuple(result)
    one,two=assembly(),assembly(plan_transform=two_axes,rows=rows)
    assert len(one.axes)==1 and len(two.axes)==2 and one.disposition==two.disposition=='ready'
    with pytest.raises(FitnessError,match='comparison_context_mismatch'):one.dominates(two)
    with pytest.raises(FitnessError,match='comparison_context_mismatch'):two.dominates(one)


@pytest.mark.parametrize('eligibility',['contradicted','unknown'])
def test_numerically_best_value_cannot_bypass_a_required_action_gate(eligibility):
    bounded=assembly('-100',eligibility_status=eligibility)
    ready=assembly('1')
    assert bounded.axes[0].amount < ready.axes[0].amount
    assert bounded.disposition in {'excluded','unavailable'}
    with pytest.raises(FitnessError,match='comparison_requires_ready'):bounded.dominates(ready)
    with pytest.raises(FitnessError,match='comparison_requires_ready'):ready.dominates(bounded)
