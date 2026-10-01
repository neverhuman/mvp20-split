from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_contracts_evidence import ObserveSourceIdentity
from amphora_contracts_research import IdentityResolution
from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.acquisition.provenance import ProvenanceError
from amphora_data_artifacts.acquisition.research import ResearchLookupError
from amphora_data_artifacts.acquisition.workflow import AcquisitionWorkflow
from amphora_data_artifacts.api import create_app
from amphora_data_artifacts.publication.model import UploadError
from fastapi.testclient import TestClient
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres
LAB = b'{"candidate_id":"c1","candidate_revision":"1","sample_id":"s1","sample_revision":"1","value":"12"}'


class Peer:
    def __init__(self, matched=False, barrier=None):
        self.matched, self.barrier, self.calls = matched, barrier, 0

    def resolve(self, query):
        self.calls += 1
        if self.barrier:
            self.barrier.wait(timeout=5)
        return IdentityResolution(wire_version="1", scope=query.scope, candidate=query.candidate, sample=query.sample,
                                  disposition="matched" if self.matched else "quarantined",
                                  reason="exact_identity_only" if self.matched else "unknown_sample", authority="identity_only")


@pytest.fixture
def observe(ingestion):
    e = ingestion

    def prepare(raw=LAB, format="synthetic_lab_json"):
        source = e.source(raw, format)
        prepared = e.workflow.prepare(e.principal, source)
        output = e.publish(prepared.content, prepared.output_schema)
        trace = e.workflow.retain(e.principal, source, "trace", output)
        return ObserveSourceIdentity(wire_version="1", observation_id="observation", trace=trace)

    return e, prepare


def test_unknown_snapshot_replays_after_peer_knowledge_changes(observe):
    e, prepare = observe
    request = prepare()
    peer = Peer()
    e.workflow.research = peer
    first = e.workflow.observe(e.principal, request)
    assert first.resolution.reason == "unknown_sample" and first.scientific_authority == "none"
    peer.matched = True
    replacement = AcquisitionWorkflow(e.reads, e.ledger, peer)
    assert replacement.observe(e.principal, request) == first and peer.calls == 1
    later = replacement.observe(e.principal, request.model_copy(update={"observation_id": "later"}))
    assert later.resolution.disposition == "matched" and peer.calls == 2
    assert e.ledger.trace_history(e.principal, "trace").disposition == "quarantined"
    assert replacement.observations.history(e.principal, "observation").result == first


@pytest.mark.parametrize("raw,format,kind", [
    (b"notes", "utf8_document", "not_applicable"),
    (b'{"value":"12"}', "synthetic_lab_json", "unresolved"),
])
def test_nonqueryable_sources_do_not_call_peer(observe, raw, format, kind):
    e, prepare = observe
    request = prepare(raw, format)
    peer = Peer()
    e.workflow.research = peer
    result = e.workflow.observe(e.principal, request)
    assert result.kind == kind and result.resolution is None and peer.calls == 0


def test_unavailable_lookup_keeps_intent_and_explicit_retry(observe):
    e, prepare = observe
    request = prepare()
    with pytest.raises(ResearchLookupError, match="research_not_configured"):
        e.workflow.observe(e.principal, request)
    state = e.workflow.observations.history(e.principal, request.observation_id)
    assert state.request == request and state.result is None
    e.workflow.research = Peer(True)
    assert e.workflow.observe(e.principal, request).resolution.disposition == "matched"


def test_request_identity_scope_and_grants_are_not_widened(observe):
    e, prepare = observe
    request = prepare(b"notes", "utf8_document")
    for actions in ({"read"}, {"acquire"}):
        with pytest.raises(UploadError, match="access_denied"):
            e.workflow.observe(replace(e.principal, actions=frozenset(actions)), request)
    foreign = replace(e.principal, scope=e.principal.scope.model_copy(update={"project_id": "foreign"}))
    with pytest.raises(ProvenanceError, match="observation_scope_mismatch"):
        e.workflow.observe(foreign, request)
    wrong = request.model_copy(update={"trace": request.trace.model_copy(update={"sha256": "0" * 64})})
    with pytest.raises(ProvenanceError, match="observation_trace_mismatch"):
        e.workflow.observe(e.principal, wrong)
    assert e.workflow.observations.history(e.principal, request.observation_id) is None
    e.workflow.observe(e.principal, request)
    with pytest.raises(ProvenanceError, match="observation_identity_conflict"):
        e.workflow.observe(e.principal, wrong)
    assert e.workflow.observations.history(foreign, request.observation_id) is None


def test_concurrent_lookup_returns_one_immutable_winner(observe):
    e, prepare = observe
    request = prepare()
    barrier = Barrier(2)
    owners = [AcquisitionWorkflow(e.reads, e.ledger, Peer(matched, barrier)) for matched in (True, False)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda owner: owner.observe(e.principal, request), owners))
    assert results[0] == results[1]
    assert e.workflow.observations.history(e.principal, request.observation_id).result == results[0]


def test_result_failure_rolls_back_without_erasing_intent(observe):
    e, prepare = observe
    request = prepare()
    e.workflow.research = Peer()

    def fail_result(_conn, _cursor, statement, _parameters, _context, _many):
        if statement.startswith("INSERT INTO artifacts.identity_observation_results"):
            raise RuntimeError("injected_result_failure")

    event.listen(e.env.engine, "before_cursor_execute", fail_result)
    try:
        with pytest.raises(RuntimeError, match="injected_result_failure"):
            e.workflow.observe(e.principal, request)
    finally:
        event.remove(e.env.engine, "before_cursor_execute", fail_result)
    assert e.workflow.observations.history(e.principal, request.observation_id).result is None
    result = e.workflow.observe(e.principal, request)
    assert e.workflow.observations.history(e.principal, request.observation_id).result == result
    for table in ("identity_observation_intents", "identity_observation_results"):
        for operation in (f"DELETE FROM artifacts.{table} WHERE false",
                          f"UPDATE artifacts.{table} SET canonical_bytes=decode('00','hex') WHERE false"):
            with pytest.raises(DBAPIError) as error, e.env.engine.begin() as connection:
                connection.execute(text(operation))
            assert error.value.orig.sqlstate == "42501"


def test_public_pending_observation_then_immutable_result(observe):
    e, prepare = observe
    command = prepare()
    headers = {"Authorization": "Bearer " + "x" * 32}
    credentials = Credentials([("x" * 32, e.principal)])
    with TestClient(create_app(e.env.uploads, e.env.storage, credentials, acquisition=e.workflow)) as client:
        route = "/v1/acquisition/identity-observations"
        assert client.post(route, json=command.model_dump(mode="json")).status_code == 401
        assert client.post(route, json=command.model_dump(mode="json"), headers=headers).status_code == 503
        pending = client.get(route + "/observation", headers=headers)
        assert pending.status_code == 200 and pending.json()["result"] is None
        e.workflow.research = Peer(True)
        response = client.post(route, json=command.model_dump(mode="json"), headers=headers)
        assert response.status_code == 200 and response.json()["scientific_authority"] == "none"
        assert client.get(route + "/observation", headers=headers).json()["result"] == response.json()
        assert client.get(route + "/absent", headers=headers).status_code == 404


def test_substituted_peer_identity_cannot_be_persisted(observe):
    e, prepare = observe
    request = prepare()

    class SubstitutedPeer(Peer):
        def resolve(self, query):
            result = super().resolve(query)
            return result.model_copy(update={"sample": result.sample.model_copy(update={"sample_id": "other"})})

    e.workflow.research = SubstitutedPeer(True)
    with pytest.raises(ResearchLookupError, match="research_binding_mismatch"):
        e.workflow.observe(e.principal, request)
    assert e.workflow.observations.history(e.principal, request.observation_id).result is None
