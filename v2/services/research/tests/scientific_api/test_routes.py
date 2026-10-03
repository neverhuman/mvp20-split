"""Real configured host and private PostgreSQL; public HTTP peer proof remains B1.08d."""
import pytest
from amphora_contracts_research import ScientificDecisionSelection, ScientificPublicationRequest
from amphora_research.transport.host import ResearchHost
from fastapi.testclient import TestClient

from ..observations.test_intake_store import stored_case
from .test_store import prepared

pytestmark = pytest.mark.postgres


def configuration(scope, actions):
    return {"database_url_env":"SCIENCE_DB","principals":[{"token_env":"SCIENCE_TOKEN","actor_id":"fixture",
        "scope":scope.model_dump(mode="json"),"actions":actions}],
        "science":{"lab_profiles":[],"eligibility_profiles":[],"synthesis_profiles":[],
            "data":{"endpoint":"http://127.0.0.1:1","token_env":"SCIENCE_READ_TOKEN"},
            "publication":{"actor_id":"publisher","token_env":"SCIENCE_PUBLISH_TOKEN"},"consumer_publishers":[]}}


def secrets(monkeypatch, engine):
    monkeypatch.setenv("SCIENCE_DB",engine.url.render_as_string(hide_password=False))
    for name in ("SCIENCE_TOKEN","SCIENCE_READ_TOKEN","SCIENCE_PUBLISH_TOKEN"):
        monkeypatch.setenv(name,"s"*32)


def test_historical_reads_and_separate_grants_without_active_profiles(ledger,monkeypatch):
    store,resolved,_ = prepared(ledger)
    bound = resolved.bound
    store.begin(bound)
    result = store.complete(bound,resolved)
    secrets(monkeypatch,store.engine)
    config = configuration(bound.configured.scope,["read_scientific_assessment","read_scientific_record","read_scientific_impact","read_scientific_publication"])
    monkeypatch.setenv("SCIENCE_OTHER_TOKEN","o"*32)
    config["principals"].append(config["principals"][0]|{"token_env":"SCIENCE_OTHER_TOKEN","actor_id":"other"})
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            headers = {"Authorization":"Bearer "+"s"*32}
            assert client.get("/health").json()["authority"] == "synthetic_science"
            response = client.post("/v1/scientific-assessments/read",headers=headers,json=bound.request.model_dump(mode="json"))
            assert response.status_code == 200 and response.json() == result.status.model_dump(mode="json")
            assert response.headers["cache-control"] == "no-store"
            response = client.post("/v1/scientific-assessments",headers=headers,json=bound.request.model_dump(mode="json"))
            assert response.status_code == 403
            assert response.headers["cache-control"] == "no-store"
            decision = result.decision.reference
            response = client.post("/v1/scientific-decisions/read",headers=headers,json=decision.model_dump(mode="json"))
            assert response.status_code == 200
            response = client.post("/v1/scientific-decisions/read",headers={"Authorization":"Bearer "+"o"*32},json=decision.model_dump(mode="json"))
            assert response.status_code == 403
            response = client.post("/v1/scientific-assessments/read",headers={"Authorization":"Bearer "+"o"*32},json=bound.request.model_dump(mode="json"))
            assert response.status_code == 403
            publication = ScientificPublicationRequest(wire_version="1",target=ScientificDecisionSelection(kind="decision",reference=decision))
            response = client.post("/v1/scientific-publications/read",headers=headers,json=publication.model_dump(mode="json"))
            assert response.status_code == 404
            response = client.post("/v1/scientific-impact",headers=headers,json={"wire_version":"1","source":bound.request.reports[0].model_dump(mode="json"),"after":None,"limit":1})
            assert response.status_code == 200 and response.json()["policy"] == "future_campaigns_only"
            assert response.json()["decisions"] == [decision.model_dump(mode="json")]
            response = client.post("/v1/scientific-consumers/read",headers=headers,json={"wire_version":"1","decision":decision.model_dump(mode="json"),"after":None,"limit":1})
            assert response.status_code == 200 and response.json()["consumers"] == []
            assert client.post("/v1/scientific-assessments/read",json=bound.request.model_dump(mode="json")).status_code == 401
            altered = bound.request.model_copy(update={"reports":(bound.request.reports[0].model_copy(update={"artifact_id":"different"}),)})
            assert client.post("/v1/scientific-assessments/read",headers=headers,json=altered.model_dump(mode="json")).status_code == 409
            for content,status in ((b'{"duplicate":1,"duplicate":2}',422),(b'{"x":NaN}',422),(b' '*262145,413)):
                response = client.post("/v1/scientific-assessments/read",headers=headers|{"Content-Type":"application/json"},content=content)
                assert response.status_code == status and response.headers["cache-control"] == "no-store"
            assert client.post("/v1/scientific-assessments/read",headers=headers,content=b'{}').status_code == 415
    finally:
        host.close()


def test_science_grants_require_optional_configuration(ledger,monkeypatch):
    identities,scope = ledger
    secrets(monkeypatch,identities.engine)
    config = configuration(scope,["assess_eligibility"])
    del config["science"]
    with pytest.raises(ValueError,match="science_configuration_required"):
        ResearchHost.configured(config)


@pytest.mark.parametrize("mutation",[
    lambda c:c["science"].update(consumer_publishers=["duplicate","duplicate"]),
    lambda c:c["science"]["data"].update(endpoint="https://external.invalid"),
    lambda c:c["science"].update(eligibility_profiles={}),
])
def test_invalid_science_configuration_is_rejected(ledger,monkeypatch,mutation):
    identities,scope = ledger
    secrets(monkeypatch,identities.engine)
    config = configuration(scope,["read_scientific_record"])
    mutation(config)
    with pytest.raises(ValueError):
        ResearchHost.configured(config)


@pytest.mark.parametrize("kind",["eligibility","synthesis"])
def test_submission_uses_own_grant_and_preserves_original_actor(ledger,monkeypatch,kind):
    store,resolved,_ = prepared(ledger,kind)
    bound = resolved.bound
    secrets(monkeypatch,store.engine)
    config = configuration(bound.configured.scope,["assess_"+kind,"read_scientific_assessment"])
    config["science"][kind+"_profiles"] = [bound.configured.document.model_dump(mode="json")]
    monkeypatch.setattr("amphora_research.scientific_api.workflow.ScientificInputResolver.resolve",lambda self,accepted:resolved)
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            headers = {"Authorization":"Bearer "+"s"*32}
            response = client.post("/v1/scientific-assessments",headers=headers,json=bound.request.model_dump(mode="json"))
            assert response.status_code == 200 and response.json()["outcome"]["status"] == "assessed"
            assert response.json()["actor_id"] == "fixture"
            assert client.post("/v1/scientific-assessments",headers=headers,json=bound.request.model_dump(mode="json")).content == response.content
            foreign = bound.request.model_dump(mode="json")
            foreign["profile"]["kind"] = "synthesis" if kind == "eligibility" else "eligibility"
            assert client.post("/v1/scientific-assessments",headers=headers,json=foreign).status_code == 403
    finally:
        host.close()


def test_partial_lab_submit_and_observation_read_preserve_quality(ledger,monkeypatch):
    store,intent,resolved = stored_case(ledger)
    scope = intent.request.profile.scope
    secrets(monkeypatch,store.engine)
    config = configuration(scope,["submit_lab_intake","read_lab_intake","read_scientific_record"])
    config["science"]["lab_profiles"] = [intent.configured.document.model_dump(mode="json")]
    monkeypatch.setattr("amphora_research.scientific_api.workflow.LabReportResolver.resolve",lambda *args:resolved)
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            headers = {"Authorization":"Bearer "+"s"*32}
            response = client.post("/v1/lab-intakes",headers=headers,json=intent.request.model_dump(mode="json"))
            assert response.status_code == 200
            body = response.json()
            assert body["outcome"]["resolution"]["disposition"] == "partial"
            selection = {"kind":"lab-intake","scope":scope.model_dump(mode="json"),"intake_id":intent.request.intake_id}
            assert client.post("/v1/lab-intakes/read",headers=headers,json=selection).json() == body
            observation = body["outcome"]["resolution"]["observations"][0]
            read = client.post("/v1/observations/read",headers=headers,json=observation["reference"])
            assert read.status_code == 200 and read.json() == observation
    finally:
        host.close()


@pytest.mark.parametrize("reason,status",[("offline",503),("denied",403),("invalid",422)])
def test_source_errors_remain_operational_and_leave_intent_pending(ledger,monkeypatch,reason,status):
    from amphora_research.assessment.policy import AssessmentError
    from amphora_research.assessment.reader import AssessmentPeerUnavailable
    from amphora_research.scientific_api.boundary import ScientificInputError
    store,resolved,_ = prepared(ledger)
    bound = resolved.bound
    secrets(monkeypatch,store.engine)
    config = configuration(bound.configured.scope,["assess_eligibility","read_scientific_assessment"])
    config["science"]["eligibility_profiles"] = [bound.configured.document.model_dump(mode="json")]
    def fail(*_):
        raise {"offline":AssessmentPeerUnavailable("offline"),"denied":AssessmentError("peer_access_denied"),
            "invalid":ScientificInputError("scientific_report_issuer_mismatch")}[reason]
    monkeypatch.setattr("amphora_research.scientific_api.workflow.ScientificInputResolver.resolve",fail)
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            headers = {"Authorization":"Bearer "+"s"*32}
            response = client.post("/v1/scientific-assessments",headers=headers,json=bound.request.model_dump(mode="json"))
            assert response.status_code == status and response.headers["cache-control"] == "no-store"
            response = client.post("/v1/scientific-assessments/read",headers=headers,json=bound.request.model_dump(mode="json"))
            assert response.status_code == 200 and response.json()["outcome"] == {"status":"pending"}
    finally:
        host.close()
