"""Actual immutable preparation storage and atomic links to candidate/sample identity."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from amphora_contracts_research import MaterialFeatureEvidence, MaterialFeatureRecord, MissingMeasurement
from amphora_research.identity.questions import ResearchIdentityError
from amphora_research.material_state.store import MaterialStateStore
from amphora_research.persistence.revisions import ScientificStoreError
from sqlalchemy import event, text

from .storage_fixtures import publish_candidate, records

pytestmark = pytest.mark.postgres


def test_material_replay_corrections_and_replacement_preserve_original_actor(ledger):
    identities,scope = ledger
    first,plan,_ = records(scope)
    publish_candidate(identities,first)
    store = MaterialStateStore(identities.engine)
    assert store.publish(scope,"original-author",first) == first
    second = first.model_copy(update={"reference":first.reference.model_copy(update={"revision":2}),"supersedes":first.reference})
    store.publish(scope,"correction-author",second)
    replacement = MaterialStateStore(identities.engine)
    assert replacement.publish(scope,"replaying-author",first) == first
    assert replacement.read(scope,first.reference) == first
    assert replacement.read(scope,second.reference) == second
    identities.publish(scope,plan.samples[0].sample)
    with identities.engine.connect() as connection:
        row = connection.execute(text("SELECT actor_id FROM research.material_state_revisions WHERE tenant_id=:t AND project_id=:p AND revision=1"),
                                 {"t":scope.tenant_id,"p":scope.project_id}).scalar_one()
        assert row == "original-author"
        assert connection.execute(text("SELECT count(*) FROM research.sample_material_states WHERE tenant_id=:t AND project_id=:p"),
                                  {"t":scope.tenant_id,"p":scope.project_id}).scalar_one() == 1


def test_unknown_candidate_and_head_jump_leave_no_material_record(ledger):
    identities,scope = ledger
    first,_,_ = records(scope)
    store = MaterialStateStore(identities.engine)
    with pytest.raises(ScientificStoreError,match="unknown_material_candidate"):
        store.publish(scope,"fixture",first)
    assert store.read(scope,first.reference) is None
    publish_candidate(identities,first)
    store.publish(scope,"fixture",first)
    skipped = first.model_copy(update={"reference":first.reference.model_copy(update={"revision":3}),
                                      "supersedes":first.reference.model_copy(update={"revision":2})})
    with pytest.raises(ScientificStoreError,match="scientific_revision_head_conflict"):
        store.publish(scope,"fixture",skipped)
    assert store.read(scope,skipped.reference) is None


def test_sample_correction_keeps_the_original_preparation_link(ledger):
    identities,scope = ledger
    first,plan,_ = records(scope)
    publish_candidate(identities,first)
    store = MaterialStateStore(identities.engine)
    store.publish(scope,"fixture",first)
    sample = plan.samples[0].sample
    identities.publish(scope,sample)
    second = first.model_copy(update={"reference":first.reference.model_copy(update={"revision":2}),"supersedes":first.reference})
    store.publish(scope,"fixture",second)
    corrected = sample.model_copy(update={"reference":sample.reference.model_copy(update={"revision":2}),
                                          "supersedes":sample.reference,"material_state":second.reference})
    identities.publish(scope,corrected)
    assert identities.read(scope,"sample",sample.reference.sample_id,1).material_state == first.reference
    assert identities.read(scope,"sample",sample.reference.sample_id,2).material_state == second.reference
    with identities.engine.connect() as connection:
        links = connection.execute(text("SELECT sample_revision,state_revision FROM research.sample_material_states "
            "WHERE tenant_id=:t AND project_id=:p ORDER BY sample_revision"),{"t":scope.tenant_id,"p":scope.project_id}).all()
        assert links == [(1,1),(2,2)]


def test_two_material_writers_cannot_overwrite_each_other(ledger):
    identities,scope = ledger
    first,_,_ = records(scope)
    publish_candidate(identities,first)
    store = MaterialStateStore(identities.engine)
    store.publish(scope,"fixture",first)
    barrier = Barrier(2)
    def publish(reason):
        value = first.model_copy(update={"reference":first.reference.model_copy(update={"revision":2}),"supersedes":first.reference,
            "features":(MaterialFeatureRecord(name="morphology",value=MissingMeasurement(kind="missing",reason=reason),
                evidence=MaterialFeatureEvidence(basis="unknown",method=None,source=None)),)})
        barrier.wait(timeout=5)
        try:
            store.publish(scope,"fixture",value)
            return "published"
        except ScientificStoreError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(publish,("left","right"))) == ["immutable_scientific_revision_conflict","published"]
    assert store.read(scope,first.reference.model_copy(update={"revision":2})).features[0].value.reason in ("left","right")


def test_sample_cannot_borrow_state_from_another_candidate(ledger):
    identities,scope = ledger
    state,plan,_ = records(scope)
    candidate = publish_candidate(identities,state)
    other = candidate.model_copy(update={"reference":candidate.reference.model_copy(update={"candidate_id":"other"})})
    identities.publish(scope,other)
    MaterialStateStore(identities.engine).publish(scope,"fixture",state)
    wrong = plan.samples[0].sample.model_copy(update={"candidate":other.reference})
    with pytest.raises(ResearchIdentityError,match="sample_material_candidate_mismatch"):
        identities.publish(scope,wrong)
    assert identities.read(scope,"sample",wrong.reference.sample_id,1) is None


@pytest.mark.parametrize("target",["research.material_state_candidates","research.sample_material_states"])
def test_link_failure_rolls_back_new_record_and_old_identity_head(ledger,target):
    identities,scope = ledger
    state,plan,_ = records(scope)
    publish_candidate(identities,state)
    store = MaterialStateStore(identities.engine)
    if target.endswith("sample_material_states"):
        store.publish(scope,"fixture",state)
    def fail(connection,cursor,statement,parameters,context,executemany):
        if statement.startswith("INSERT INTO "+target):
            raise RuntimeError("fixture_link_failure")
    event.listen(identities.engine,"before_cursor_execute",fail)
    try:
        with pytest.raises(RuntimeError,match="fixture_link_failure"):
            if target.endswith("sample_material_states"):
                identities.publish(scope,plan.samples[0].sample)
            else:
                store.publish(scope,"fixture",state)
    finally:
        event.remove(identities.engine,"before_cursor_execute",fail)
    if target.endswith("sample_material_states"):
        assert identities.read(scope,"sample",plan.samples[0].sample.reference.sample_id,1) is None
        assert identities.publish(scope,plan.samples[0].sample) == plan.samples[0].sample
    else:
        assert store.read(scope,state.reference) is None
        assert store.publish(scope,"fixture",state) == state
