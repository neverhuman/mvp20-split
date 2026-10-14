from dataclasses import replace

import pytest
from amphora_contracts_population import population_record_schema
from amphora_evolution_search.population import GenerationMembership, SelectedGeneration, SuccessorContinuity


def verify(case, proposal=None, **changes):
    fields = {key: case[key] for key in ("source", "birth_manifest", "birth_payloads", "cohort", "cohort_reference", "pool", "pool_reference", "evaluations")}
    fields.update(changes)
    fields["artifact"] = case["artifact"]("proposal", population_record_schema("population.proposed-successor"), proposal or case["proposal"])
    return SuccessorContinuity.verify(**fields)


def test_exact_parent_union_and_rng_replay(successor_case):
    result = verify(successor_case)
    assert len(result.births) == 2
    assert result.record.generation.predecessor == result.source.artifact.reference
    assert result.record.rng.counter > result.source.record.rng.counter


@pytest.mark.parametrize("field", ["predecessor", "run_id", "generation"])
def test_wrong_predecessor_identity_rejects(successor_case, field):
    record = successor_case["proposal"]
    replacement = {"predecessor": record.selection, "run_id": "foreign-run", "generation": 2}[field]
    with pytest.raises(ValueError, match="successor_predecessor"):
        verify(successor_case, record.model_copy(update={"generation": record.generation.model_copy(update={field: replacement})}))


@pytest.mark.parametrize("field,value,code", [("evaluations_reserved", 5, "successor_evaluation_budget"),
                                            ("disposition", "evaluation_budget", "successor_disposition")])
def test_validly_hashed_false_accounting_rejects(successor_case, field, value, code):
    with pytest.raises(ValueError, match=code):
        verify(successor_case, successor_case["proposal"].model_copy(update={field: value}))


def test_rng_tail_and_missing_selected_parent_reject(successor_case):
    record = successor_case["proposal"]
    with pytest.raises(ValueError, match="successor_rng_tail"):
        verify(successor_case, record.model_copy(update={"rng": record.rng.model_copy(update={"counter": record.rng.counter + 1})}))
    pool = successor_case["pool"]
    incomplete = GenerationMembership(pool.original, pool.identity, pool.role, tuple(m for m in pool.members if m.candidate_id != successor_case["source"].decision.selected[0]))
    with pytest.raises(ValueError, match="successor_parent_union"):
        verify(successor_case, pool=incomplete)


@pytest.mark.parametrize("change,code", [({"rng": "bad"}, "checkpoint_rng_position"),
                                       ({"evaluations_terminal": 3}, "checkpoint_terminal_progress"),
                                       ({"attempts_issued": 12001}, "checkpoint_work_budget")])
def test_checkpoint_requires_completed_cut_and_budget_position(successor_case, change, code):
    case = successor_case; record = case["checkpoint"]
    if "rng" in change:
        record = record.model_copy(update={"rng": record.rng.model_copy(update={"counter": 1})})
    else:
        record = record.model_copy(update={"progress": record.progress.model_copy(update=change)})
    with pytest.raises(ValueError, match=code):
        SelectedGeneration.verify(case["artifact"]("checkpoint", population_record_schema("population.checkpoint"), record),
            case["selection"], case["decision"], case["old_pool_ref"], case["fitness_ref"], case["parents"])


def test_exhausted_predecessor_cannot_continue(successor_case):
    source = successor_case["source"]
    progress = source.record.progress.model_copy(update={"attempts_issued": source.decision.pool.original.record.budget.max_attempts})
    stopped = replace(source, record=source.record.model_copy(update={"progress": progress}))
    assert stopped.stop_reason == "attempt_budget"
    with pytest.raises(ValueError, match="successor_stopped_predecessor"):
        verify(successor_case, source=stopped)
