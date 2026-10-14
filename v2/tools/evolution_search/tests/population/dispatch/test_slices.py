import hashlib

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import membership_manifest_schema, population_record_schema, population_specification_schema
from amphora_contracts_population_steps import PreparedPopulationGeneration, population_step_schema
from amphora_evolution_search.population import DeclaredEvaluations, PopulationArtifact, canonical
from amphora_evolution_search.population.dispatch import PreparedGeneration


@pytest.fixture
def prepared(born_cohort):
    cohort = born_cohort
    declarations = DeclaredEvaluations.primary(cohort)
    def artifact(name, schema, record=None):
        raw = canonical(record) if record is not None else b"{}"
        return PopulationArtifact(ArtifactRef(artifact_id=name, scope=cohort.identity.scope, schema_ref=schema,
            media_type="application/json", sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)), raw)
    spec = artifact("spec", population_specification_schema()).reference
    members = artifact("cohort", membership_manifest_schema()).reference
    births = artifact("births", population_record_schema("population.birth-manifest")).reference
    slots = artifact("slots", population_record_schema("population.evaluation-declarations")).reference
    record = PreparedPopulationGeneration(schema_version="1", generation=cohort.identity, specification=spec,
                                         births=births, cohort=members, declarations=slots)
    return PreparedGeneration.verify(artifact("prepared", population_step_schema("population-step.prepared"), record),
        declarations, spec, members, births, slots), artifact


def test_candidate_slices_preserve_whole_membership_across_batching(prepared):
    source, _ = prepared
    one = (*source.slice(0, 1).contexts, *source.slice(1, 1).contexts)
    two = source.slice(0, 2)
    assert one == two.contexts
    assert two.next_index == 2 and two.complete
    empty = source.slice(2, 1)
    assert empty.contexts == () and empty.complete
    assert source.slice(0, 1).complete is False
    with pytest.raises(ValueError, match="dispatch_start"):
        source.slice(3, 1)
    with pytest.raises(ValueError, match="dispatch_slice_budget"):
        source.slice(0, source.declarations.membership.original.record.budget.dispatch_slice + 1)


def test_false_cursor_complete_or_member_cannot_be_published(prepared):
    source, artifact = prepared
    sliced = source.slice(0, 1)
    contexts = tuple(artifact("context" + str(i), population_step_schema("population-step.candidate-context"), c)
                     for i, c in enumerate(sliced.contexts))
    record = sliced.bind(contexts)
    sliced.verify(record, contexts)
    for changed in ({"complete": True}, {"next_index": 2}, {"members": ()}):
        with pytest.raises(ValueError, match="dispatch_slice_replay"):
            sliced.verify(record.model_copy(update=changed), contexts)
    wrong = artifact("wrong", population_step_schema("population-step.candidate-context"), source.slice(1, 1).contexts[0])
    with pytest.raises(ValueError, match="dispatch_context_binding"):
        sliced.bind((wrong,))
