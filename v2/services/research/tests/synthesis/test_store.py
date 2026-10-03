"""Synthesis alternatives preserve exact history and share only private journal mechanics."""
import pytest
from amphora_research.persistence.decision_index import DecisionIndex
from amphora_research.synthesis import wire
from amphora_research.synthesis.store import SynthesisStore

from ..material_state.storage_fixtures import in_scope, publish_candidate, records
from .test_policy import option, policy

pytestmark = pytest.mark.postgres


def prepared_case(ledger):
    identities,scope = ledger
    state,_,_ = records(scope)
    publish_candidate(identities,state)
    configured = wire.profile_from_wire(in_scope(wire.profile_to_wire(policy()),scope))
    options = tuple(wire.option_from_wire(in_scope(wire.option_to_wire(item),scope))
                    for item in (option("blocked",status="failed"),option("useful")))
    return SynthesisStore(identities.engine),configured,options


def test_independent_rebuild_retains_alternatives_and_source_impacts(ledger):
    store,configured,options = prepared_case(ledger)
    result = store.assess(configured,options,"fixture","decision")
    assert [item.disposition for item in result.assessment.alternatives] == ["blocked","eligible"]
    replacement = SynthesisStore(store.journal.engine)
    assert replacement.read(result.reference.scope,result.reference) == result
    assert replacement.assess(configured,options,"fixture","decision") == result
    page = DecisionIndex(store.journal.engine).affected(result.reference.scope,options[0].evidence.route)
    assert page.decisions == (result.reference,)
    different = options[0].evidence.route.model_copy(update={"sha256":"0"*64})
    assert not DecisionIndex(store.journal.engine).affected(result.reference.scope,different).decisions
