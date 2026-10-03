"""Actual persistence indexes exact observations and leaves prior decisions unchanged on correction."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_contracts_research import ObservationQuality
from amphora_research.eligibility import wire
from amphora_research.eligibility.store import EligibilityStore
from amphora_research.observations.store import ObservationStore
from amphora_research.persistence.decision_document import DecisionStoreError
from amphora_research.persistence.decision_index import DecisionIndex

from ..material_state.storage_fixtures import in_scope, publish_specimen
from .test_policy import claim, policy

pytestmark = pytest.mark.postgres


def prepared_case(ledger):
    identities,scope = ledger
    state,experiment,observation = publish_specimen(identities,scope)
    ObservationStore(identities.engine).publish(scope,"fixture",observation)
    profile = in_scope(wire.profile_to_wire(policy()),scope)
    profile = profile.model_copy(update={"context":profile.context.model_copy(update={"subject":profile.context.subject.model_copy(update={
        "candidate":state.candidate,"material_state":state.reference,"sample":experiment.samples[0].sample.reference})})})
    record = in_scope(wire.claim_to_wire(claim()),scope)
    record = record.model_copy(update={"context":profile.context,"origin":record.origin.model_copy(update={
        "source":observation.source,"observation":observation.reference})})
    return EligibilityStore(identities.engine),wire.profile_from_wire(profile),(wire.claim_from_wire(record),),observation


def test_exact_decision_replay_and_correction_impact_preserve_historical_result(ledger):
    store,configured,claims,observation = prepared_case(ledger)
    result = store.assess(configured,claims,"fixture","decision")
    scope = result.reference.scope
    assert result.assessment.disposition == "eligible" and result.assessment.focus == ("accuracy",)
    assert EligibilityStore(store.journal.engine).read(scope,result.reference) == result
    assert store.assess(configured,claims,"fixture","decision") == result
    corrected = observation.model_copy(update={"reference":observation.reference.model_copy(update={"revision":2}),
        "supersedes":observation.reference,"quality":ObservationQuality(controls="failed",flags=("low_accuracy",))})
    ObservationStore(store.journal.engine).publish(scope,"fixture",corrected)
    index = DecisionIndex(store.journal.engine)
    affected = index.affected(scope,observation.reference)
    assert affected.policy == "future_campaigns_only" and affected.decisions == (result.reference,)
    assert not index.affected(scope,corrected.reference).decisions
    assert store.read(scope,result.reference) == result


def test_concurrent_replay_and_conflicting_policy_actor_are_immutable(ledger):
    store,configured,claims,_ = prepared_case(ledger)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _:store.assess(configured,claims,"fixture","decision"),range(2)))
    assert results[0] == results[1]
    for actor,changed in (("other",configured),("fixture",replace(configured,requirements=(configured.requirements[0],)))):
        with pytest.raises(DecisionStoreError,match="immutable_scientific_decision_conflict"):
            store.assess(changed,claims,actor,"decision")


@pytest.mark.parametrize("mutation,reason",[
    (lambda c:replace(c,origin=replace(c.origin,observation=replace(c.origin.observation,revision=2))),"unknown_decision_observation"),
    (lambda c:replace(c,origin=replace(c.origin,source=c.origin.source.model_copy(update={"artifact_id":"forged-source"}))),"decision_observation_source_mismatch"),
])
def test_invalid_observation_dependency_cannot_leave_partial_decision(ledger,mutation,reason):
    store,configured,claims,observation = prepared_case(ledger)
    with pytest.raises(DecisionStoreError,match=reason):
        store.assess(configured,(mutation(claims[0]),),"fixture","decision")
    assert not DecisionIndex(store.journal.engine).affected(observation.reference.scope,observation.reference).decisions
    assert store.assess(configured,claims,"fixture","decision").assessment.disposition == "eligible"


def test_foreign_scope_and_wrong_digest_cannot_read_decision(ledger):
    store,configured,claims,_ = prepared_case(ledger)
    result = store.assess(configured,claims,"fixture","decision")
    with pytest.raises(DecisionStoreError,match="scientific_decision_reference_scope"):
        store.read(result.reference.scope.model_copy(update={"project_id":"other"}),result.reference)
    with pytest.raises(DecisionStoreError,match="scientific_decision_digest_mismatch"):
        store.read(result.reference.scope,result.reference.model_copy(update={"sha256":"0"*64}))


@pytest.mark.parametrize("field,reason",[
    ("candidate","unknown_decision_candidate"),("material_state","decision_material_candidate_mismatch"),
    ("sample","unknown_decision_sample"),
])
def test_unknown_subject_revision_does_not_create_a_decision(ledger,field,reason):
    store,configured,claims,observation = prepared_case(ledger)
    subject = configured.context.subject
    changed = replace(subject,**{field:getattr(subject,field).model_copy(update={"revision":2})})
    wrong = replace(configured,context=replace(configured.context,subject=changed))
    with pytest.raises(DecisionStoreError,match=reason):
        store.assess(wrong,claims,"fixture","decision")
    assert not DecisionIndex(store.journal.engine).affected(observation.reference.scope,observation.source).decisions


def test_sample_cannot_silently_drop_its_known_state(ledger):
    store,configured,claims,_ = prepared_case(ledger)
    wrong = replace(configured,context=replace(configured.context,subject=replace(configured.context.subject,material_state=None)))
    with pytest.raises(DecisionStoreError,match="decision_sample_context_mismatch"):
        store.assess(wrong,claims,"fixture","decision")


def test_unknown_optional_state_without_sample_is_preserved(ledger):
    store,configured,_,_ = prepared_case(ledger)
    unknown = replace(configured,context=replace(configured.context,subject=replace(configured.context.subject,material_state=None,sample=None)))
    result = store.assess(unknown,(),"fixture","decision")
    assert result.assessment.disposition == "unknown" and result.assessment.policy.context.subject.material_state is None


def test_postcommit_reply_loss_preserves_first_outcome_on_retry(ledger):
    store,configured,claims,_ = prepared_case(ledger)
    def lost():
        store.assess(configured,claims,"fixture","decision")
        raise ConnectionError("local reply lost after commit")
    with pytest.raises(ConnectionError):
        lost()
    result = EligibilityStore(store.journal.engine).assess(configured,claims,"fixture","decision")
    assert result.actor_id == "fixture" and result.assessment.disposition == "eligible"


def test_model_evidence_keeps_source_dependency_without_inventing_observation(ledger):
    store,configured,claims,observation = prepared_case(ledger)
    configured = replace(configured,requirements=(replace(configured.requirements[0],kind="model"),))
    model_claim = replace(claims[0],origin=replace(claims[0].origin,kind="model",observation=None))
    result = store.assess(configured,(model_claim,),"fixture","model-decision")
    assert result.assessment.disposition == "eligible" and result.observations == ()
    index = DecisionIndex(store.journal.engine)
    assert index.affected(result.reference.scope,observation.source).decisions == (result.reference,)
    assert not index.affected(result.reference.scope,observation.reference).decisions
