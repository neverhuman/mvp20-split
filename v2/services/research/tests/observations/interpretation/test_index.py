"""Known exact dependencies survive corrections without altering any result or campaign state."""
import pytest
from amphora_research.observations.identity import ObservationError
from amphora_research.observations.interpretation.index import InterpretationIndex

from .test_storage import prepared_case

pytestmark = pytest.mark.postgres


def test_source_observation_and_material_indexes_have_exact_bounded_pagination(ledger):
    store,profile,request = prepared_case(ledger)
    results = []
    for name in ("b","a","c"):
        prepared = store.prepare(store.begin(profile,request.model_copy(update={"interpretation_id":name}),"actor").intent)
        results.append(store.complete(prepared,prepared.sources).result)
    index = InterpretationIndex(store.engine)
    sources = (prepared.sources[0],request.observations[0],prepared.material_states[0])
    for source in sources:
        first = index.affected(profile.scope,source,limit=2)
        assert first.policy == "future_campaigns_only" and first.interpretations == (results[1].reference,results[0].reference)
        last = index.affected(profile.scope,source,after=first.next_after,limit=2)
        assert last.interpretations == (results[2].reference,) and last.next_after is None
    assert not index.affected(profile.scope,prepared.sources[0].model_copy(update={"size_bytes":12345})).interpretations
    assert not index.affected(profile.scope,request.observations[0].model_copy(update={"revision":2})).interpretations
    assert not index.affected(profile.scope,prepared.material_states[0].model_copy(update={"revision":2})).interpretations
    assert store.read(profile.scope,"actor",profile.kind,"a").result == results[1]


def test_scope_digest_and_page_bounds_are_not_implicit_latest_selection(ledger):
    store,profile,request = prepared_case(ledger)
    prepared = store.prepare(store.begin(profile,request,"actor").intent)
    result = store.complete(prepared,prepared.sources).result
    index = InterpretationIndex(store.engine)
    for limit in (0,129,True):
        with pytest.raises(ObservationError,match="page_limit"):
            index.affected(profile.scope,prepared.sources[0],limit=limit)
    other = profile.scope.model_copy(update={"project_id":"other"})
    with pytest.raises(ObservationError,match="source_scope"):
        index.affected(other,prepared.sources[0])
    with pytest.raises(ObservationError,match="cursor_scope"):
        index.affected(profile.scope,prepared.sources[0],after=result.reference.model_copy(update={"scope":other}))
    with pytest.raises(ObservationError,match="digest_mismatch"):
        index.affected(profile.scope,prepared.sources[0],after=result.reference.model_copy(update={"sha256":"0"*64}))
