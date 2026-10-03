"""Read-only exact correction history remains available after subsequent revisions."""
import pytest
from amphora_contracts_research import ObservationQuality
from amphora_research.observations.correction_views import ObservationCorrectionViews
from amphora_research.observations.identity import ObservationError
from amphora_research.observations.store import ObservationStore
from amphora_research.persistence.revisions import ScientificStoreError

from ..material_state.storage_fixtures import records

pytestmark = pytest.mark.postgres


def test_exact_successor_view_keeps_original_and_corrected_quality_without_head_selection(ledger):
    identities,scope = ledger
    _,_,first = records(scope)
    store = ObservationStore(identities.engine)
    views = ObservationCorrectionViews(identities.engine)
    assert views.read(scope,first.reference) is None
    store.publish(scope,"fixture",first)
    with pytest.raises(ObservationError,match="no_predecessor"):
        views.read(scope,first.reference)
    second = first.model_copy(update={"reference":first.reference.model_copy(update={"revision":2}),"supersedes":first.reference,
        "quality":ObservationQuality(controls="failed",flags=("low_accuracy",))})
    third = second.model_copy(update={"reference":first.reference.model_copy(update={"revision":3}),"supersedes":second.reference,
        "quality":ObservationQuality(controls="passed",flags=())})
    for row in (second,third):
        store.publish(scope,"fixture",row)
    result = views.read(scope,second.reference)
    assert result.before == first and result.after == second and result.changed_fields == ("quality",)
    assert result.policy == "future_campaigns_only" and views.read(scope,third.reference).before == second
    with pytest.raises(ScientificStoreError,match="scope_or_reference"):
        views.read(scope.model_copy(update={"project_id":"other"}),second.reference)
