"""Chemical declaration tests; retained tool output is a fixture, not peer evidence."""
import hashlib
import json
from pathlib import Path
import pytest
from amphora_contracts_core import ArtifactRef, SchemaRef, Scope
from amphora_contracts_research import CandidateRevision, CandidateRevisionRef
from amphora_research.candidate_registration.chemical_profile import ChemicalCandidateProfile
from amphora_research.candidate_registration.profiles import CandidateProfile, CandidateProfiles, CandidateRegistrationError, schema_reference
from amphora_research.candidate_registration.registration import CandidateRegistrar, CandidateReader
from amphora_research.assessment.policy import AssessmentError
from amphora_research.transport.access import Principal


def fixture(scope=None):
    data=json.loads(Path(__file__).with_name("chemical-result.json").read_bytes())
    if scope:
        data["scope"]=scope.model_dump(); data["candidate"]["scope"]=scope.model_dump()
    profile=ChemicalCandidateProfile(schema_reference("chemical-structure.result"),"finite_molecule",SchemaRef.model_validate(data["semantic_profile"]))
    return data,profile


def artifact(data,profile):
    body=json.dumps(data).encode()
    return ArtifactRef(artifact_id="chemical-fixture",scope=Scope.model_validate(data["scope"]),sha256=hashlib.sha256(body).hexdigest(),size_bytes=len(body),media_type="application/json",schema_ref=profile.schema),body


def test_explicit_profile_and_exact_identity_required():
    data,profile=fixture(); reference,body=artifact(data,profile)
    candidate=CandidateRevisionRef.model_validate(data["candidate"])
    assert CandidateProfiles([profile]).validate(reference,body,candidate).candidate==candidate
    for wrong in (None,candidate.model_copy(update={"revision":2}),candidate.model_copy(update={"candidate_id":"other"})):
        with pytest.raises(CandidateRegistrationError,match="exact_identity"):
            CandidateProfiles([profile]).validate(reference,body,wrong)
    with pytest.raises(CandidateRegistrationError): CandidateProfile(profile.schema,"finite_molecule",profile.semantic_profile)

@pytest.mark.parametrize("mutation",["failure","scope","profile","png-hash","png-size","graph-index","bond-ref","charge"])
def test_malformed_or_foreign_bundle_rejected(mutation):
    data,profile=fixture(); candidate=CandidateRevisionRef.model_validate(data["candidate"])
    out=data["outcome"]
    if mutation=="failure": data["outcome"]={"status":"unsupported","code":"unsupported_feature"}
    elif mutation=="scope": data["candidate"]["scope"]["project_id"]="other"
    elif mutation=="profile": data["semantic_profile"]["sha256"]="f"*64
    elif mutation=="png-hash": out["depiction"]["sha256"]="f"*64
    elif mutation=="png-size": out["depiction"]["width"]=1
    elif mutation=="graph-index": out["graph"]["atoms"][0]["index"]=3
    elif mutation=="bond-ref": out["graph"]["bonds"][0]["end"]=511
    elif mutation=="charge": out["formula"]["net_formal_charge"]=1
    reference,body=artifact(data,profile)
    with pytest.raises(CandidateRegistrationError): CandidateProfiles([profile]).validate(reference,body,candidate)


def test_multiple_explicit_profiles_and_published_schema():
    data,profile=fixture(); reference,body=artifact(data,profile)
    wrong=ChemicalCandidateProfile(profile.schema,"finite_molecule",profile.semantic_profile.model_copy(update={"sha256":"f"*64}))
    candidate=CandidateRevisionRef.model_validate(data["candidate"])
    assert CandidateProfiles([wrong,profile]).validate(reference,body,candidate).candidate==candidate
    root=Path(__file__).absolute().parents[4]
    assert hashlib.sha256((root/"contracts/schemas/v1/chemical-structure.result.validation.json").read_bytes()).hexdigest()==profile.schema.sha256


@pytest.mark.postgres
def test_chemical_retry_denial_history_and_revision_binding(ledger):
    store,scope=ledger; data,profile=fixture(scope); reference,body=artifact(data,profile)
    record=CandidateRevision(wire_version="1",reference=CandidateRevisionRef.model_validate(data["candidate"]),representation=reference,supersedes=None)
    class Reader:
        calls=0
        denied=False
        def read(self,ref):
            self.calls+=1
            if self.denied: raise AssessmentError("peer_access_denied")
            assert ref==reference
            return body
    reader=Reader(); principal=Principal("chemical-declarer",scope,frozenset({"declare_candidate","read_candidate"}))
    registrar=CandidateRegistrar(store,CandidateProfiles([profile]),lambda _:reader)
    assert registrar.register(principal,record)==record
    assert registrar.register(principal,record)==record and reader.calls==2
    wrong=record.model_copy(update={"reference":record.reference.model_copy(update={"revision":2}),"supersedes":record.reference})
    with pytest.raises(CandidateRegistrationError,match="exact_identity"): registrar.register(principal,wrong)
    reader.denied=True
    with pytest.raises(CandidateRegistrationError,match="peer_access_denied"): registrar.register(principal,record)
    assert CandidateReader(store).read(principal,record.reference)==record


@pytest.mark.postgres
def test_explicit_chemical_host_configuration(research_database,monkeypatch):
    from amphora_research.transport.host import ResearchHost
    data,profile=fixture()
    monkeypatch.setenv("CHEMICAL_DB",research_database.render_as_string(hide_password=False))
    monkeypatch.setenv("CHEMICAL_TOKEN","c"*32)
    monkeypatch.setenv("CHEMICAL_DATA_TOKEN","d"*32)
    config={"database_url_env":"CHEMICAL_DB","principals":[{"token_env":"CHEMICAL_TOKEN","actor_id":"chemical-actor","scope":data["scope"],"actions":["declare_candidate","read_candidate"]}],"candidates":{"data":{"endpoint":"http://127.0.0.1:1","token_env":"CHEMICAL_DATA_TOKEN"},"profiles":[{"schema":profile.schema.model_dump(),"kind":profile.kind,"semantic_profile":profile.semantic_profile.model_dump()}]}}
    host=ResearchHost.configured(config)
    try:
        assert host.app.state.candidates_enabled
        assert "/v1/candidates" in {route.path for route in host.app.routes}
    finally: host.close()
    config["candidates"]["profiles"][0]["kind"]="chemical_guess"
    with pytest.raises(CandidateRegistrationError): ResearchHost.configured(config)
