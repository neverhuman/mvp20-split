"""Material correction views preserve exact preparation/features and immutable history."""
import pytest
from amphora_contracts_research import MaterialFeatureEvidence, MaterialFeatureRecord, MissingMeasurement
from amphora_research.material_state.correction_views import MaterialStateCorrectionViews
from amphora_research.material_state.store import MaterialStateStore
from amphora_research.material_state.validation import MaterialStateError
from amphora_research.persistence.revisions import ScientificStoreError

from .storage_fixtures import publish_specimen

pytestmark = pytest.mark.postgres


def test_material_view_is_exact_transition_not_latest_or_equivalent_candidate(ledger):
    identities,scope = ledger
    first,_,_ = publish_specimen(identities,scope)
    views = MaterialStateCorrectionViews(identities.engine)
    assert views.read(scope,first.reference.model_copy(update={"material_state_id":"missing"})) is None
    with pytest.raises(MaterialStateError,match="no_predecessor"):
        views.read(scope,first.reference)
    second = first.model_copy(update={"reference":first.reference.model_copy(update={"revision":2}),"supersedes":first.reference,
        "features":(MaterialFeatureRecord(name="morphology",value=MissingMeasurement(kind="missing",reason="unverified"),
            evidence=MaterialFeatureEvidence(basis="unknown",method=None,source=None)),)})
    store = MaterialStateStore(identities.engine)
    store.publish(scope,"fixture",second)
    result = views.read(scope,second.reference)
    assert result.policy == "future_campaigns_only" and result.before == first and result.after == second
    assert result.changed_fields == ("features",) and result.before.candidate == result.after.candidate
    with pytest.raises(ScientificStoreError,match="scope_or_reference"):
        views.read(scope.model_copy(update={"project_id":"other"}),second.reference)
