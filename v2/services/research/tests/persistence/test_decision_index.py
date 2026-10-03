"""Exact bounded impact/consumer pages, with no mutation or inferred global dependents."""
import pytest
from amphora_research.persistence.decision_document import DecisionStoreError
from amphora_research.persistence.decision_index import DecisionIndex
from sqlalchemy import text

from ..eligibility.test_store import prepared_case

pytestmark = pytest.mark.postgres


def test_impact_pages_do_not_drop_dependencies_or_include_other_revision(ledger):
    store,configured,claims,observation = prepared_case(ledger)
    results = tuple(store.assess(configured,claims,"fixture",name) for name in ("b","a","c"))
    scope = results[0].reference.scope
    index = DecisionIndex(store.journal.engine)
    first = index.affected(scope,observation.reference,limit=2)
    assert [item.decision_id for item in first.decisions] == ["a","b"]
    assert first.next_after == results[0].reference
    second = index.affected(scope,observation.reference,after=first.next_after,limit=2)
    assert second.decisions == (results[2].reference,) and second.next_after is None
    assert not index.affected(scope,observation.reference.model_copy(update={"revision":2})).decisions
    assert index.affected(scope,observation.source).decisions == (results[1].reference,results[0].reference,results[2].reference)


def test_explicit_consumers_are_immutable_bounded_and_preserve_first_actor(ledger):
    store,configured,claims,observation = prepared_case(ledger)
    result = store.assess(configured,claims,"fixture","decision")
    scope,ref = result.reference.scope,result.reference
    index = DecisionIndex(store.journal.engine)
    consumers = tuple(observation.source.model_copy(update={"artifact_id":name}) for name in ("consumer-b","consumer-a","consumer-c"))
    assert index.consumers(scope,ref).consumers == ()
    for consumer in consumers:
        assert index.register_consumer(scope,"first-actor",ref,consumer) == consumer
    assert index.register_consumer(scope,"another-authorized-actor",ref,consumers[0]) == consumers[0]
    with pytest.raises(DecisionStoreError,match="immutable_scientific_consumer_conflict"):
        index.register_consumer(scope,"first-actor",ref,consumers[0].model_copy(update={"sha256":"0"*64}))
    first = index.consumers(scope,ref,limit=2)
    assert first.consumers == (consumers[1],consumers[0]) and first.next_after == "consumer-b"
    last = index.consumers(scope,ref,after=first.next_after,limit=2)
    assert last.consumers == (consumers[2],) and last.next_after is None
    with store.journal.engine.connect() as connection:
        actors = connection.execute(text("SELECT DISTINCT actor_id FROM research.decision_consumers WHERE tenant_id=:tenant AND project_id=:project"),
            {"tenant":scope.tenant_id,"project":scope.project_id}).scalars().all()
        assert actors == ["first-actor"]
    assert store.read(scope,ref) == result


def test_unknown_digest_scope_and_page_boundaries_fail_explicitly(ledger):
    store,configured,claims,observation = prepared_case(ledger)
    result = store.assess(configured,claims,"fixture","decision")
    scope,ref = result.reference.scope,result.reference
    index = DecisionIndex(store.journal.engine)
    for limit in (0,129,True):
        with pytest.raises(DecisionStoreError,match="scientific_index_page_limit"):
            index.affected(scope,observation.source,limit=limit)
        with pytest.raises(DecisionStoreError,match="scientific_index_page_limit"):
            index.consumers(scope,ref,limit=limit)
    for changed,reason in ((ref.model_copy(update={"decision_id":"unknown"}),"unknown_consumer_decision"),
                           (ref.model_copy(update={"sha256":"0"*64}),"scientific_decision_digest_mismatch")):
        with pytest.raises(DecisionStoreError,match=reason):
            index.register_consumer(scope,"fixture",changed,observation.source)
        with pytest.raises(DecisionStoreError,match=reason):
            index.consumers(scope,changed)
    other = scope.model_copy(update={"project_id":"other"})
    with pytest.raises(DecisionStoreError,match="scientific_impact_source_scope"):
        index.affected(other,observation.source)
    with pytest.raises(DecisionStoreError,match="scientific_consumer_scope"):
        index.register_consumer(scope,"fixture",ref,observation.source.model_copy(update={"scope":other}))
    with pytest.raises(DecisionStoreError,match="scientific_decision_reference_scope"):
        index.affected(scope,observation.source,after=ref.model_copy(update={"scope":other}))


def test_journals_are_append_only_and_revision_width_matches_owner(ledger):
    identities,_ = ledger
    with identities.engine.connect() as connection:
        for table in ("scientific_decisions","decision_sources","decision_observations","decision_consumers"):
            for privilege in ("UPDATE","DELETE","TRUNCATE","REFERENCES","TRIGGER"):
                assert not connection.execute(text("SELECT has_table_privilege(current_user,:table,:privilege)"),
                    {"table":f"research.{table}","privilege":privilege}).scalar_one()
        assert connection.execute(text("SELECT data_type FROM information_schema.columns WHERE table_schema='research' "
            "AND table_name='lab_observations' AND column_name='revision'")).scalar_one() == "bigint"
