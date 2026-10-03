"""Actual owner transactions; fixture evidence is private, not an authentication proof."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_contracts_research import ScientificAssessmentRequest
from amphora_research.eligibility import wire as eligibility_wire
from amphora_research.persistence.decision_index import DecisionIndex
from amphora_research.scientific_api.boundary import ConfiguredScientificInput, ScientificInputError
from amphora_research.scientific_api.resolution import ResolvedScientificInput
from amphora_research.scientific_api.store import ScientificInputStore
from amphora_research.synthesis import wire as synthesis_wire
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from ..eligibility.test_store import prepared_case as eligibility_case
from ..material_state.storage_fixtures import in_scope
from ..synthesis.test_store import prepared_case as synthesis_case
from .test_resolution import resolution_case

pytestmark = pytest.mark.postgres


def prepared(ledger,kind="eligibility"):
    identities,scope = ledger
    owner,policy,evidence,*_ = (eligibility_case if kind == "eligibility" else synthesis_case)(ledger)
    template,_ = resolution_case(kind)
    wire = eligibility_wire if kind == "eligibility" else synthesis_wire
    profile = in_scope(template.configured.document,scope).model_copy(update={"policy":wire.profile_to_wire(policy)})
    configured = ConfiguredScientificInput(profile)
    report = in_scope(template.request.reports[0],scope)
    request = ScientificAssessmentRequest(wire_version="1",decision_id="scientific-input",profile=configured.reference,reports=(report,))
    bound = configured.bind(request,"fixture",scope)
    initial = ResolvedScientificInput(bound,evidence,())
    inputs = tuple(dict.fromkeys((*initial.decision_document().record.sources,report)))
    return ScientificInputStore(identities.engine),replace(initial,inputs=inputs),owner


@pytest.mark.parametrize("kind",["eligibility","synthesis"])
def test_pinned_intent_concurrent_completion_and_replacement(ledger,kind):
    store,resolved,_ = prepared(ledger,kind)
    bound = resolved.bound
    assert store.begin(bound).status.outcome.status == "pending"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _:store.complete(bound,resolved),range(2)))
    assert results[0] == results[1]
    replacement = ScientificInputStore(store.engine)
    assert replacement.read(bound.configured.scope,bound.actor,kind,bound.request.decision_id) == results[0]
    assert replacement.begin(bound) == results[0]
    assert DecisionIndex(store.engine).affected(bound.configured.scope,bound.request.reports[0]).decisions == (results[0].decision.reference,)
    with pytest.raises(ScientificInputError,match="actor_mismatch"):
        replacement.read(bound.configured.scope,"other",kind,bound.request.decision_id)
    assert replacement.read(bound.configured.scope.model_copy(update={"project_id":"absent"}),bound.actor,kind,bound.request.decision_id) is None


def test_unassociated_private_decision_is_not_a_completed_submission(ledger):
    store,resolved,owner = prepared(ledger)
    bound = resolved.bound
    owner.assess(bound.configured.policy,resolved.evidence,bound.actor,bound.request.decision_id,consumed=resolved.inputs)
    assert store.begin(bound).decision is None
    assert store.complete(bound,resolved).decision is not None


def test_terminal_insert_failure_rolls_back_decision_and_indexes(ledger):
    store,resolved,_ = prepared(ledger)
    bound = resolved.bound
    store.begin(bound)
    def fail(connection,cursor,statement,parameters,context,many):
        if statement.startswith("INSERT INTO research.scientific_input_outcomes"):
            raise RuntimeError("outcome storage unavailable")
    event.listen(store.engine,"before_cursor_execute",fail)
    try:
        with pytest.raises(RuntimeError,match="outcome storage"):
            store.complete(bound,resolved)
    finally:
        event.remove(store.engine,"before_cursor_execute",fail)
    assert store.decisions.read(bound.configured.scope,resolved.decision_document().record.reference) is None
    assert not DecisionIndex(store.engine).affected(bound.configured.scope,bound.request.reports[0]).decisions
    assert store.begin(bound).decision is None
    assert store.complete(bound,resolved).decision is not None


def test_conflicting_actor_request_and_postcommit_reply_loss(ledger):
    store,resolved,_ = prepared(ledger)
    bound = resolved.bound
    with pytest.raises(ScientificInputError,match="not_started"):
        store.complete(bound,resolved)
    store.begin(bound)
    for altered in (replace(bound,actor="other"),replace(bound,request=bound.request.model_copy(update={
        "reports":(bound.request.reports[0].model_copy(update={"artifact_id":"other"}),)}))):
        with pytest.raises(ScientificInputError,match="identity_conflict"):
            store.begin(altered)
    def lose_reply():
        store.complete(bound,resolved)
        raise ConnectionError("reply lost")
    with pytest.raises(ConnectionError):
        lose_reply()
    assert store.begin(bound).decision == store.complete(bound,resolved).decision


@pytest.mark.parametrize("table",["scientific_input_intents","scientific_input_outcomes"])
def test_application_cannot_mutate_or_delete_history(ledger,table):
    store,resolved,_ = prepared(ledger)
    store.begin(resolved.bound)
    store.complete(resolved.bound,resolved)
    for statement in (f"DELETE FROM research.{table}",f"UPDATE research.{table} SET decision_id='changed'"):
        with pytest.raises(DBAPIError):
            with store.engine.begin() as connection:
                connection.execute(text(statement+" WHERE tenant_id=:tenant AND project_id=:project"),resolved.bound.key)
