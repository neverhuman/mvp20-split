"""Unmatched and corrected reports remain immutable without fabricated acceptance."""
import pytest
from amphora_contracts_research import ObservationQuality, ObservationTarget
from amphora_research.observations.store import ObservationStore
from amphora_research.persistence.revisions import ScientificStoreError

from ..material_state.storage_fixtures import records

pytestmark = pytest.mark.postgres


def test_unmatched_return_and_correction_survive_replacement(ledger):
    identities,scope = ledger
    _,_,original = records(scope)
    first = original.model_copy(update={"binding":original.binding.model_copy(update={"target":ObservationTarget(experiment=None,expectation_id=None,replicate_id=None)})})
    store = ObservationStore(identities.engine)
    assert store.publish(scope,"fixture",first) == first
    second = first.model_copy(update={"reference":first.reference.model_copy(update={"revision":2}),"supersedes":first.reference,
        "quality":ObservationQuality(controls="failed",flags=("questionable","low_accuracy"))})
    store.publish(scope,"fixture",second)
    replacement = ObservationStore(identities.engine)
    assert replacement.publish(scope,"fixture",first) == first
    assert replacement.read(scope,first.reference).quality.controls == "unknown"
    assert replacement.read(scope,second.reference).quality.flags == ("questionable","low_accuracy")
    assert replacement.read(scope,first.reference).binding.target.experiment is None


def test_scope_and_revision_collision_do_not_change_history(ledger):
    identities,scope = ledger
    _,_,first = records(scope)
    store = ObservationStore(identities.engine)
    other = scope.model_copy(update={"project_id":"other"})
    with pytest.raises(ScientificStoreError,match="scientific_record_scope_mismatch"):
        store.publish(other,"fixture",first)
    store.publish(scope,"fixture",first)
    with pytest.raises(ScientificStoreError,match="scientific_read_scope_or_reference"):
        store.read(other,first.reference)
    changed = first.model_copy(update={"quality":ObservationQuality(controls="failed",flags=())})
    with pytest.raises(ScientificStoreError,match="immutable_scientific_revision_conflict"):
        store.publish(scope,"fixture",changed)
    assert store.read(scope,first.reference) == first
