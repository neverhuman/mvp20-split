"""Cumulative progress counts physical work separately and compares parent fronts."""
from types import SimpleNamespace

import pytest
from amphora_evolution_search.population_workers.assembly import PrimaryAssembly
from amphora_evolution_search.population_workers.selection_evidence import SelectionEvidence

from .test_successor_fitness import parent_only_case


def evidence_case(e):
    subject, source = parent_only_case(e)
    pool = PrimaryAssembly.selection_pool(subject)
    evidence = SelectionEvidence(original=pool.pool.original, prepared=subject.prepared,
        evaluations=SimpleNamespace(frozen=SimpleNamespace(keys=(1,2,3,4))),
        fitness=SimpleNamespace(selection=pool), pages=(), observations=source.observations, successor=source)
    old = source.selected.record.progress
    counter = SimpleNamespace(attempts_issued=old.attempts_issued+7, activations_created=old.activations_created+10)
    return evidence, old, counter


def test_cumulative_progress_preserves_rng_and_compares_parent_front(worker_artifacts):
    evidence, old, counter = evidence_case(worker_artifacts)
    progress = evidence.progress(counter)
    assert progress.evaluations_issued == progress.evaluations_terminal == old.evaluations_issued+4
    assert progress.attempts_issued == old.attempts_issued+7
    assert progress.activations_created == old.activations_created+10
    assert progress.unchanged_front_generations == 1
    assert evidence.rng == evidence.successor.batch.rng.to_record()


@pytest.mark.parametrize("field", ["attempts_issued", "activations_created"])
def test_cumulative_physical_counters_cannot_regress(worker_artifacts, field):
    evidence, old, counter = evidence_case(worker_artifacts)
    setattr(counter, field, getattr(old, field)-1)
    with pytest.raises(ValueError, match="work_regressed"):
        evidence.progress(counter)
