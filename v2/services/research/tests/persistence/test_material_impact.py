"""Forward backfill, atomic trigger maintenance and exact bounded future-only decision lookup."""
import hashlib
import json
import os
from pathlib import Path

import pytest
from amphora_research.persistence.decision_document import DecisionStoreError
from amphora_research.persistence.material_impact import MaterialDecisionIndex
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from ..eligibility.test_store import prepared_case

pytestmark = pytest.mark.postgres


def test_exact_state_pages_cursor_and_historical_decision_preservation(ledger):
    store,configured,claims,_ = prepared_case(ledger)
    results = tuple(store.assess(configured,claims,"actor",name) for name in ("b","a","c"))
    state = results[0].assessment.policy.context.subject.material_state
    index = MaterialDecisionIndex(store.journal.engine)
    first = index.affected(state.scope,state,limit=2)
    assert first.policy == "future_campaigns_only" and first.decisions == (results[1].reference,results[0].reference)
    last = index.affected(state.scope,state,after=first.next_after,limit=2)
    assert last.decisions == (results[2].reference,) and last.next_after is None
    assert not index.affected(state.scope,state.model_copy(update={"revision":2})).decisions
    assert store.read(state.scope,results[0].reference) == results[0]
    for cursor,reason in ((first.next_after.model_copy(update={"sha256":"0"*64}),"digest_mismatch"),
                          (first.next_after.model_copy(update={"decision_id":"missing"}),"cursor_unknown")):
        with pytest.raises(DecisionStoreError,match=reason):
            index.affected(state.scope,state,after=cursor)
    for limit in (0,129,True):
        with pytest.raises(DecisionStoreError,match="page_limit"):
            index.affected(state.scope,state,limit=limit)
    with pytest.raises(DecisionStoreError,match="source_scope"):
        index.affected(state.scope.model_copy(update={"project_id":"other"}),state)


def test_trigger_index_and_decision_rollback_together(ledger):
    store,configured,claims,_ = prepared_case(ledger)
    def fail(connection,cursor,statement,parameters,context,many):
        if statement.startswith("INSERT INTO research.scientific_decisions"):
            raise RuntimeError("failure after triggered insert")
    event.listen(store.journal.engine,"after_cursor_execute",fail)
    try:
        with pytest.raises(RuntimeError,match="triggered"):
            store.assess(configured,claims,"actor","rollback")
    finally:
        event.remove(store.journal.engine,"after_cursor_execute",fail)
    state = configured.context.subject.material_state
    assert not MaterialDecisionIndex(store.journal.engine).affected(state.scope,state).decisions
    result = store.assess(configured,claims,"actor","rollback")
    assert MaterialDecisionIndex(store.journal.engine).affected(state.scope,state).decisions == (result.reference,)
    for statement in ("DELETE FROM research.decision_material_states","UPDATE research.decision_material_states SET state_id='other'"):
        with pytest.raises(DBAPIError):
            with store.journal.engine.begin() as connection:
                connection.execute(text(statement+" WHERE tenant_id=:tenant AND project_id=:project"),
                    {"tenant":state.scope.tenant_id,"project":state.scope.project_id})


def test_forward_backfill_preserves_existing_decision_bytes_and_exact_links(research_database):
    from sqlalchemy import create_engine

    path = os.environ.get("AMPHORA_TEST_MATERIAL_IMPACT_BASELINE")
    if not path:
        pytest.skip("Pre-migration retained-state evidence was not supplied")
    rows = json.loads(Path(path).read_text())
    assert rows
    engine = create_engine(research_database)
    try:
        with engine.connect() as connection:
            for row in rows:
                actual = connection.execute(text("SELECT d.sha256,d.canonical_bytes,i.state_id,i.state_revision "
                    "FROM research.scientific_decisions d JOIN research.decision_material_states i "
                    "USING(tenant_id,project_id,kind,decision_id) WHERE d.tenant_id=:tenant AND d.project_id=:project "
                    "AND d.kind=:kind AND d.decision_id=:id"),row).one()
                assert actual.sha256 == row["sha256"]
                assert hashlib.sha256(bytes(actual.canonical_bytes)).hexdigest() == row["canonical_sha256"]
                assert (actual.state_id,actual.state_revision) == (row["state"],row["revision"])
    finally:
        engine.dispose()
