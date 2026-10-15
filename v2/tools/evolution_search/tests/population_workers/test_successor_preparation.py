"""Prepare declared work without final future input keys or unobserved budget grants."""
import json
import pytest
from amphora_contracts_population import MembershipManifest,EvaluationDeclarationManifest,population_record_schema,membership_manifest_schema
from amphora_contracts_population_steps import PreparedPopulationGeneration,population_step_schema
from amphora_evolution_search.population_workers.method_plan import payload_schema
from amphora_evolution_search.population_workers.payloads import PrimarySuccessorDecision,PreparedPrimarySuccessor
from amphora_evolution_search.population_workers.successor_preparation import SuccessorPreparation

from .successor_fixture import successor_fixture


def test_prepared_generation_has_exact_rng_declared_slots_and_parent_union(worker_artifacts):
    e=worker_artifacts;c=successor_fixture(e)
    preparation=SuccessorPreparation.load(c.request,c.session,c.runtime)
    root=preparation.publish(c.session)
    decision=root.decode(PrimarySuccessorDecision,payload_schema(PrimarySuccessorDecision,"population-worker.successor-decision"),e.client.identity.scope)
    assert not decision.stopped and decision.reason_code is None
    detail=PreparedPrimarySuccessor.model_validate_json(e.client.contents[decision.successor.artifact_id])
    prepared=PreparedPopulationGeneration.model_validate_json(e.client.contents[detail.prepared.artifact_id])
    cohort=MembershipManifest.model_validate_json(e.client.contents[prepared.cohort.artifact_id])
    pool=MembershipManifest.model_validate_json(e.client.contents[detail.pool.artifact_id])
    declarations=EvaluationDeclarationManifest.model_validate_json(e.client.contents[prepared.declarations.artifact_id])
    assert prepared.generation.generation==1 and prepared.generation.predecessor==c.request.checkpoint
    assert detail.rng.counter==4*(1+3+3) and pool.member_count==4+cohort.member_count
    assert declarations.slot_count==detail.evaluations_planned==cohort.member_count
    assert not any(ref.schema_ref.schema_id=="population.evaluation-manifest" for ref in c.session.client.parents[detail.prepared.artifact_id])


@pytest.mark.parametrize("options,reason",[({"generations":0},"generation_budget"),({"status":"all-skipped"},"no_feasible_survivors"),
    ({"available":0},"attempt_budget")])
def test_stop_produces_no_fabricated_next_births(worker_artifacts,options,reason):
    c=successor_fixture(worker_artifacts,**options)
    preparation=SuccessorPreparation.load(c.request,c.session,c.runtime)
    result=PrimarySuccessorDecision.model_validate_json(preparation.publish(c.session).content)
    assert result.stopped and result.reason_code==reason and result.successor is None


def test_checkpoint_must_be_the_accepted_selected_output(worker_artifacts):
    c=successor_fixture(worker_artifacts)
    c.proof["completion"]["result"]["outcome"]["outputs"][0]["artifact"]["artifact_id"]="not-selected"
    with pytest.raises((ValueError,KeyError)):SuccessorPreparation.load(c.request,c.session,c.runtime)


def test_observed_capacity_can_only_reduce_legacy_default_allocation(worker_artifacts):
    from amphora_evolution_search.population.planning import PrimaryBirthBatch,EvaluationCapacity
    c=successor_fixture(worker_artifacts)
    preparation=SuccessorPreparation.load(c.request,c.session,c.runtime)
    selected=preparation.selected;budget=selected.decision.pool.original.record.budget
    remaining=EvaluationCapacity(budget.max_evaluations-selected.record.progress.evaluations_issued,
        budget.max_attempts-selected.record.progress.attempts_issued)
    assert PrimaryBirthBatch.successor(selected)==PrimaryBirthBatch.successor(selected,remaining)
    bounded=PrimaryBirthBatch.successor(selected,EvaluationCapacity(remaining.evaluations,0))
    assert not bounded.proposed and bounded.rng==PrimaryBirthBatch.successor(selected).rng
    with pytest.raises(ValueError,match="observed_capacity"):
        PrimaryBirthBatch.successor(selected,EvaluationCapacity(remaining.evaluations,remaining.attempts+1))
