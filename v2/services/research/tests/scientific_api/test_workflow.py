"""Owner storage with scripted resolvers: pending intent and offline-history semantics."""
from types import SimpleNamespace

import pytest
from amphora_research.assessment.reader import AssessmentPeerUnavailable
from amphora_research.scientific_api.boundary import ScientificInputError
from amphora_research.scientific_api.profiles import ReviewedProfiles
from amphora_research.scientific_api.workflow import LabIntakeWorkflow, ScientificAssessmentWorkflow

from ..observations.test_intake_store import stored_case
from .test_resolution import resolution_case
from .test_store import prepared


def unavailable(*_):
    raise AssessmentPeerUnavailable("offline")


def test_reviewed_registry_rejects_duplicates_and_unknown_configuration():
    bound,_ = resolution_case()
    with pytest.raises(ScientificInputError,match="duplicate"):
        ReviewedProfiles((bound.configured,bound.configured))
    with pytest.raises(ScientificInputError,match="profile_type"):
        ReviewedProfiles((object(),))
    with pytest.raises(ScientificInputError,match="unavailable"):
        ReviewedProfiles().select(bound.configured.reference)


@pytest.mark.postgres
@pytest.mark.parametrize("kind",["eligibility","synthesis"])
def test_pending_keeps_pinned_profile_and_completed_history_is_offline(ledger,monkeypatch,kind):
    store,resolved,_ = prepared(ledger,kind)
    bound = resolved.bound
    scope,actor,request = bound.configured.scope,bound.actor,bound.request
    workflow = ScientificAssessmentWorkflow(store,ReviewedProfiles((bound.configured,)),unavailable)
    with pytest.raises(AssessmentPeerUnavailable):
        workflow.submit(scope,actor,request)
    assert workflow.read(scope,actor,kind,request.decision_id).outcome.status == "pending"
    replacement = ScientificAssessmentWorkflow(store,ReviewedProfiles(),lambda _:object())
    def resolve(self,accepted):
        assert store.read(scope,actor,kind,request.decision_id).intent.bound == accepted == bound
        return resolved
    monkeypatch.setattr("amphora_research.scientific_api.workflow.ScientificInputResolver.resolve",resolve)
    result = replacement.submit(scope,actor,request)
    assert result.outcome.status == "assessed"
    offline = ScientificAssessmentWorkflow(store,ReviewedProfiles(),unavailable)
    assert offline.submit(scope,actor,request) == result
    assert offline.read(scope,actor,kind,request.decision_id) == result
    with pytest.raises(ScientificInputError,match="identity_conflict"):
        offline.submit(scope,actor,request.model_copy(update={"reports":(request.reports[0].model_copy(update={"artifact_id":"changed"}),)}))
    assert offline.read(scope,actor,kind,"absent") is None
    with pytest.raises(ScientificInputError,match="unavailable"):
        offline.submit(scope,actor,request.model_copy(update={"decision_id":"new"}))


@pytest.mark.postgres
def test_lab_partial_return_resumes_then_replays_without_sources(ledger,monkeypatch):
    store,intent,resolved = stored_case(ledger)
    scope,actor,request = intent.request.profile.scope,intent.actor,intent.request
    workflow = LabIntakeWorkflow(store,None,ReviewedProfiles((intent.configured,)),unavailable)
    with pytest.raises(AssessmentPeerUnavailable):
        workflow.submit(scope,actor,request)
    assert workflow.read(scope,actor,request.intake_id).outcome.status == "pending"
    def resolve(self,configured,source):
        assert configured == intent.configured and source == request.report
        assert store.read(scope,actor,request.intake_id).intent == intent
        return resolved
    monkeypatch.setattr("amphora_research.scientific_api.workflow.LabReportResolver.resolve",resolve)
    replacement = LabIntakeWorkflow(store,None,ReviewedProfiles(),lambda _:SimpleNamespace(consumed=()))
    result = replacement.submit(scope,actor,request)
    assert result.outcome.resolution.disposition == "partial"
    offline = LabIntakeWorkflow(store,None,ReviewedProfiles(),unavailable)
    assert offline.submit(scope,actor,request) == result
    assert offline.read(scope,actor,request.intake_id) == result
    with pytest.raises(ScientificInputError,match="identity_conflict"):
        offline.submit(scope,actor,request.model_copy(update={"report":request.report.model_copy(update={"artifact_id":"changed"})}))
    assert offline.read(scope,actor,"absent") is None


@pytest.mark.postgres
def test_lab_cannot_reuse_previous_reader_authorization(ledger):
    store,intent,_ = stored_case(ledger)
    workflow = LabIntakeWorkflow(store,None,ReviewedProfiles((intent.configured,)),lambda _:SimpleNamespace(consumed=(intent.request.report,)))
    with pytest.raises(ScientificInputError,match="reader_reused"):
        workflow.submit(intent.request.profile.scope,intent.actor,intent.request)
