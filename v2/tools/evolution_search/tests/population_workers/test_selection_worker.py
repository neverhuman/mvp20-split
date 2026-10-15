"""Whole-pool ranks, exclusions and observed counters without dispatch-order shortcuts."""
import pytest
from amphora_contracts_population import PopulationCheckpoint,PopulationSelectionReceipt,population_record_schema
from amphora_evolution_search.population_workers.method_plan import payload_schema
from amphora_evolution_search.population_workers.payloads import SelectedPrimaryGeneration
from amphora_evolution_search.population_workers.selection import InitialSelection

from .selection_fixture import selection_fixture


@pytest.mark.parametrize("status,count",[("succeeded",4),("failed",3),("all-skipped",0)])
def test_initial_selection_uses_full_pool_and_keeps_actual_physical_counts(worker_artifacts,status,count):
    e=worker_artifacts;c=selection_fixture(e,status)
    selection=InitialSelection.load(c.request,c.session,c.runtime)
    result=selection.publish(c.session)
    record=result.decode(SelectedPrimaryGeneration,payload_schema(SelectedPrimaryGeneration,"population-worker.selected"),e.client.identity.scope)
    checkpoint=PopulationCheckpoint.model_validate_json(e.client.contents[record.checkpoint.artifact_id])
    receipt=PopulationSelectionReceipt.model_validate_json(e.client.contents[record.selection.artifact_id])
    assert receipt.member_count==4 and len(receipt.selected)==count
    assert checkpoint.progress.evaluations_issued==checkpoint.progress.evaluations_terminal==4
    assert checkpoint.progress.attempts_issued==c.expected_attempts
    assert checkpoint.progress.activations_created==c.page["snapshot"]["node_count"]
    assert checkpoint.rng.counter==4*len(c.prepared.declarations.membership.original.record.variables)
    assert record.work_cut==selection.counter.cut
    if not count:assert record.stop_reason=="no_feasible_survivors" and receipt.stopped


def test_unaccepted_fitness_cannot_be_ranked(worker_artifacts):
    c=selection_fixture(worker_artifacts)
    c.proof["completion"]["result"]["outcome"]["outputs"][0]["artifact"]["artifact_id"]="unrelated"
    with pytest.raises((ValueError,KeyError)):InitialSelection.load(c.request,c.session,c.runtime)


def test_parallel_work_rejects_instead_of_guessing_checkpoint_counters(worker_artifacts):
    c=selection_fixture(worker_artifacts)
    c.page["nodes"][-1]["status"]="issued"
    with pytest.raises(ValueError,match="parallel_scope"):InitialSelection.load(c.request,c.session,c.runtime)
