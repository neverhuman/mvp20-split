"""Configured HTTP handlers over real owner storage; source readers are scripted in this tier."""
import pytest
from amphora_contracts_research import InterpretationSelection, ObservationQuality
from amphora_research.material_state.store import MaterialStateStore
from amphora_research.observations.store import ObservationStore
from amphora_research.transport.host import ResearchHost
from fastapi.testclient import TestClient

from ..eligibility.test_store import prepared_case as eligibility_case
from ..observations.interpretation.test_storage import prepared_case
from ..scientific_api.test_routes import configuration, secrets
from .test_workflow import Reader

pytestmark = pytest.mark.postgres
HEADERS = {"Authorization":"Bearer "+"s"*32}


def selection(request):
    return InterpretationSelection(scope=request.profile.scope,kind=request.kind,interpretation_id=request.interpretation_id).model_dump(mode="json")


@pytest.mark.parametrize("use",[False,True])
def test_configured_profiles_submit_exact_status_and_preserve_quality(use,ledger,monkeypatch):
    store,profile,request = prepared_case(ledger,use)
    prepared = store.prepare(store.begin(profile,request,"fixture").intent)
    request = request.model_copy(update={"interpretation_id":"new-public-job"})
    secrets(monkeypatch,store.engine)
    grant = "assess_observation_use" if use else "normalize_observation"
    config = configuration(profile.scope,[grant,"read_observation_interpretation"])
    config["science"]["observation_use_profiles" if use else "normalization_profiles"] = [profile.to_wire().model_dump(mode="json")]
    monkeypatch.setattr("amphora_research.scientific_api.host.AssessmentDataReader",lambda endpoint,token,scope:Reader(scope,prepared.sources))
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            path = "/v1/observation-uses" if use else "/v1/observation-normalizations"
            response = client.post(path,headers=HEADERS,json=request.model_dump(mode="json"))
            assert response.status_code == 200 and response.json()["outcome"]["status"] == "interpreted"
            assert response.headers["cache-control"] == "no-store" and response.json()["actor_id"] == "fixture"
            if use:
                review = response.json()["outcome"]["projection"]["reviews"][0]
                assert review["disposition"] == "usable" and "controls_unknown" in review["focus"]
            assert client.post(path,headers=HEADERS,json=request.model_dump(mode="json")).content == response.content
            assert client.post("/v1/observation-interpretations/read",headers=HEADERS,json=selection(request)).content == response.content
    finally:
        host.close()


def test_zero_active_profiles_history_grants_actor_scope_and_invalid_bodies(ledger,monkeypatch):
    store,profile,request = prepared_case(ledger)
    prepared = store.prepare(store.begin(profile,request,"fixture").intent)
    result = store.complete(prepared,prepared.sources)
    secrets(monkeypatch,store.engine)
    config = configuration(profile.scope,["read_observation_interpretation"])
    monkeypatch.setenv("SCIENCE_OTHER_TOKEN","o"*32)
    config["principals"].append(config["principals"][0]|{"token_env":"SCIENCE_OTHER_TOKEN","actor_id":"other"})
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            path = "/v1/observation-interpretations/read"
            response = client.post(path,headers=HEADERS,json=selection(request))
            assert response.status_code == 200 and response.json()["outcome"]["projection"] == result.result.model_dump(mode="json")
            assert client.post(path,json=selection(request)).status_code == 401
            assert client.post(path,headers={"Authorization":"Bearer "+"o"*32},json=selection(request)).status_code == 403
            assert client.post("/v1/observation-uses",headers=HEADERS,json=request.model_dump(mode="json")).status_code == 403
            assert client.post(path,headers=HEADERS,json=selection(request)|{"interpretation_id":"absent"}).status_code == 404
            foreign = selection(request)|{"scope":{"tenant_id":profile.scope.tenant_id,"project_id":"other"}}
            assert client.post(path,headers=HEADERS,json=foreign).status_code == 403
            for payload in (b'{"kind":"normalization","kind":"observation-use"}',b'{"x":NaN}',b'not json'):
                assert client.post(path,headers=HEADERS|{"Content-Type":"application/json"},content=payload).status_code == 422
            assert client.post(path,headers=HEADERS|{"Content-Type":"application/json"},content=b"x"*262145).status_code == 413
    finally:
        host.close()


def test_pending_outage_does_not_become_scientific_failure_and_missing_profile_is_explicit(ledger,monkeypatch):
    store,profile,request = prepared_case(ledger)
    secrets(monkeypatch,store.engine)
    config = configuration(profile.scope,["assess_observation_use","read_observation_interpretation"])
    config["science"]["observation_use_profiles"] = [profile.to_wire().model_dump(mode="json")]
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            response = client.post("/v1/observation-uses",headers=HEADERS,json=request.model_dump(mode="json"))
            assert response.status_code == 503 and response.json()["code"] == "scientific_peer_unavailable"
            status = client.post("/v1/observation-interpretations/read",headers=HEADERS,json=selection(request))
            assert status.status_code == 200 and status.json()["outcome"] == {"status":"pending"}
            unknown = request.model_copy(update={"interpretation_id":"other","profile":request.profile.model_copy(update={
                "policy":request.profile.policy.model_copy(update={"sha256":"0"*64})})})
            assert client.post("/v1/observation-uses",headers=HEADERS,json=unknown.model_dump(mode="json")).status_code == 404
    finally:
        host.close()


def test_correction_and_impact_routes_keep_exact_history_and_separate_read_grants(ledger,monkeypatch):
    store,profile,request = prepared_case(ledger)
    prepared = store.prepare(store.begin(profile,request,"fixture").intent)
    original = store.complete(prepared,prepared.sources)
    observations = ObservationStore(store.engine)
    before = observations.read(profile.scope,request.observations[0])
    after = before.model_copy(update={"reference":before.reference.model_copy(update={"revision":2}),"supersedes":before.reference,
        "quality":ObservationQuality(controls="failed",flags=("low_accuracy",))})
    observations.publish(profile.scope,"fixture",after)
    materials = MaterialStateStore(store.engine)
    prior_state = materials.read(profile.scope,prepared.material_states[0])
    next_state = prior_state.model_copy(update={"reference":prior_state.reference.model_copy(update={"revision":2}),"supersedes":prior_state.reference})
    materials.publish(profile.scope,"fixture",next_state)
    secrets(monkeypatch,store.engine)
    config = configuration(profile.scope,["read_scientific_record","read_scientific_impact","read_interpretation_impact"])
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            view = client.post("/v1/observation-corrections/read",headers=HEADERS,json=after.reference.model_dump(mode="json"))
            assert view.status_code == 200 and view.json()["changed_fields"] == ["quality"]
            assert view.json()["before"] == before.model_dump(mode="json") and view.json()["policy"] == "future_campaigns_only"
            material = client.post("/v1/material-state-corrections/read",headers=HEADERS,json=next_state.reference.model_dump(mode="json"))
            assert material.status_code == 200 and material.json()["before"] == prior_state.model_dump(mode="json")
            assert client.post("/v1/material-state-corrections/read",headers=HEADERS,json=prior_state.reference.model_dump(mode="json")).status_code == 422
            query = {"wire_version":"1","source":before.reference.model_dump(mode="json"),"after":None,"limit":128}
            impact = client.post("/v1/interpretation-impact",headers=HEADERS,json=query)
            assert impact.status_code == 200 and impact.json()["interpretations"] == [original.result.reference.model_dump(mode="json")]
            query["source"] = prior_state.reference.model_dump(mode="json")
            state_impact = client.post("/v1/material-state-impact",headers=HEADERS,json=query)
            assert state_impact.status_code == 200 and state_impact.json()["decisions"] == []
            assert client.post("/v1/observation-interpretations/read",headers=HEADERS,json=selection(request)).status_code == 403
    finally:
        host.close()


def test_material_impact_route_exposes_existing_eligibility_dependency(ledger,monkeypatch):
    store,policy,claims,_ = eligibility_case(ledger)
    decision = store.assess(policy,claims,"fixture","decision")
    state = decision.assessment.policy.context.subject.material_state
    secrets(monkeypatch,store.journal.engine)
    host = ResearchHost.configured(configuration(state.scope,["read_scientific_impact"]))
    try:
        with TestClient(host.app) as client:
            query = {"wire_version":"1","source":state.model_dump(mode="json"),"after":None,"limit":128}
            response = client.post("/v1/material-state-impact",headers=HEADERS,json=query)
            assert response.status_code == 200 and response.json()["decisions"] == [decision.reference.model_dump(mode="json")]
            assert client.post("/v1/interpretation-impact",headers=HEADERS,json=query).status_code == 403
    finally:
        host.close()


@pytest.mark.parametrize("variant",["wrong_type","oversized","combined_bound","duplicate","bad_hash","unknown_field"])
def test_optional_profile_configuration_is_strict_and_bounded(ledger,monkeypatch,variant):
    store,profile,_ = prepared_case(ledger)
    secrets(monkeypatch,store.engine)
    config = configuration(profile.scope,["assess_observation_use"])
    document = profile.to_wire().model_dump(mode="json")
    config["science"]["observation_use_profiles"] = [document]
    if variant == "wrong_type":
        config["science"]["observation_use_profiles"] = {}
    elif variant == "oversized":
        config["science"]["observation_use_profiles"] *= 33
    elif variant == "combined_bound":
        from amphora_research.observations.interpretation.profiles import InterpretationProfile

        from ..observations.normalization.test_catalog import catalog

        config["science"]["observation_use_profiles"] *= 17
        config["science"]["normalization_profiles"] = [InterpretationProfile(profile.scope,catalog()).to_wire().model_dump(mode="json")]*17
    elif variant == "duplicate":
        config["science"]["observation_use_profiles"] *= 2
    elif variant == "bad_hash":
        document["policy"]["reference"]["sha256"] = "0"*64
    else:
        config["science"]["allow_unreviewed"] = True
    with pytest.raises(ValueError):
        ResearchHost.configured(config)
