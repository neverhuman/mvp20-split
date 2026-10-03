"""Actual experiment storage validates embedded records against immutable owner history."""
import pytest
from amphora_research.experiments.store import ExperimentStore
from amphora_research.persistence.revisions import ScientificStoreError
from sqlalchemy import event

from ..material_state.storage_fixtures import publish_specimen, records

pytestmark = pytest.mark.postgres


def test_experiment_replacement_and_unknown_state_preserve_exact_sample(ledger):
    identities,scope = ledger
    _,plan,_ = publish_specimen(identities,scope)
    store = ExperimentStore(identities.engine)
    assert store.publish(scope,"fixture",plan) == plan
    second = plan.model_copy(update={"reference":plan.reference.model_copy(update={"revision":2}),"supersedes":plan.reference,
        "samples":(plan.samples[0].model_copy(update={"state":None}),)})
    store.publish(scope,"fixture",second)
    replacement = ExperimentStore(identities.engine)
    assert replacement.read(scope,plan.reference) == plan
    assert replacement.publish(scope,"fixture",plan) == plan
    assert replacement.read(scope,second.reference).samples[0].state is None


def test_unpersisted_sample_cannot_create_experiment_history(ledger):
    identities,scope = ledger
    _,plan,_ = records(scope)
    store = ExperimentStore(identities.engine)
    with pytest.raises(ScientificStoreError,match="unknown_experiment_sample"):
        store.publish(scope,"fixture",plan)
    assert store.read(scope,plan.reference) is None


@pytest.mark.parametrize("component,reason",[("sample","experiment_sample_record_mismatch"),("state","experiment_state_record_mismatch")])
def test_claimed_same_reference_cannot_replace_persisted_content(ledger,component,reason):
    identities,scope = ledger
    _,plan,_ = publish_specimen(identities,scope)
    item = plan.samples[0]
    if component == "sample":
        wrong = item.model_copy(update={"sample":item.sample.model_copy(update={"identity_evidence":item.sample.identity_evidence.model_copy(update={"artifact_id":"different"})})})
    else:
        wrong = item.model_copy(update={"state":item.state.model_copy(update={"supersedes":None,"candidate":item.state.candidate,
            "features":()})})
        # Change source-independent state meaning while retaining its exact reference.
        from amphora_contracts_research import (
            MaterialFeatureEvidence,
            MaterialFeatureRecord,
            MissingMeasurement,
        )
        wrong = wrong.model_copy(update={"state":wrong.state.model_copy(update={"features":(
            MaterialFeatureRecord(name="unknown",value=MissingMeasurement(kind="missing",reason="different"),
                                  evidence=MaterialFeatureEvidence(basis="unknown",method=None,source=None)),)})})
    store = ExperimentStore(identities.engine)
    with pytest.raises(ScientificStoreError,match=reason):
        store.publish(scope,"fixture",plan.model_copy(update={"samples":(wrong,)}))
    assert store.read(scope,plan.reference) is None


def test_experiment_link_failure_is_atomic(ledger):
    identities,scope = ledger
    _,plan,_ = publish_specimen(identities,scope)
    store = ExperimentStore(identities.engine)
    def fail(connection,cursor,statement,parameters,context,executemany):
        if statement.startswith("INSERT INTO research.experiment_samples"):
            raise RuntimeError("fixture_link_failure")
    event.listen(identities.engine,"before_cursor_execute",fail)
    try:
        with pytest.raises(RuntimeError,match="fixture_link_failure"):
            store.publish(scope,"fixture",plan)
    finally:
        event.remove(identities.engine,"before_cursor_execute",fail)
    assert store.read(scope,plan.reference) is None
    assert store.publish(scope,"fixture",plan) == plan
