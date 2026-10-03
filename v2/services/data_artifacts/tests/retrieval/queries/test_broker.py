"""Actual Data/PostgreSQL broker, using a labeled test-only search port."""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier
from types import SimpleNamespace

import pytest
from amphora_contracts_evidence import SourceSpan
from amphora_contracts_representations import EncodeSourceRequest, RetrieveRepresentations
from amphora_data_artifacts.acquisition.provenance import SourceDocument
from amphora_data_artifacts.representations.bindings.workflow import BindingWorkflow
from amphora_data_artifacts.retrieval.manifest import point_id
from amphora_data_artifacts.retrieval.mapping import reference_to_wire
from amphora_data_artifacts.retrieval.queries.broker import RetrievalBroker
from amphora_data_artifacts.retrieval.queries.mapping import policy_to_wire
from amphora_data_artifacts.retrieval.queries.policy import QueryPolicy
from amphora_data_artifacts.retrieval.validation import RetrievalError
from amphora_data_artifacts.source_rights.ledger import SourceRights
from amphora_data_artifacts.source_rights.model import RightsError
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from ..test_generation_publication import revoke, rows

pytestmark = pytest.mark.postgres


@pytest.fixture
def query(projection):
    e = projection
    e.publication.build_and_verify(e.p, e.lease)
    e.publication.publish(e.p, e.lease)
    # Independent query provenance must remain usable when corpus rights are revoked.
    source = e.source.model_copy(update={
        "reference": e.source.reference.model_copy(update={"source_id": "query-source", "raw": e.ingestion.publish(b"BAAB")}),
        "delivery": e.source.delivery.model_copy(update={"delivery_id": "query-delivery"}),
        "rights": e.source.rights.model_copy(update={"rights_id": "query-rights"}),
    })
    rights = SourceRights(e.engine)
    old = rights.history(e.p, e.source.rights.rights_id, 1)
    rights.publish(e.p, old.model_copy(update={"reference": source.rights}))
    e.ingestion.ledger.register(e.p, source, SourceDocument(source.reference, b"BAAB"))
    encode = EncodeSourceRequest(wire_version="1", encoding_id="query-encoding", profile=e.request.profile,
        source=SourceSpan(source=source.reference, unit="byte", start=0, end=4, sha256=hashlib.sha256(b"BAAB").hexdigest()))
    e.query_binding = BindingWorkflow(e.ingestion.reads, e.ingestion.env.uploads, e.ingestion.env.storage).encode(e.p, encode).outcome.binding
    e.search_calls = []
    e.after_query = lambda: None
    e.observations = lambda values: values

    def search(namespace, values, allowed):
        e.search_calls.append((namespace, allowed))
        points = e.backend_port.snapshots[namespace].points
        observed = tuple(SimpleNamespace(point=p, score=sum(a*b for a,b in zip(values,p.values,strict=True))) for p in reversed(points) if p.point_id in allowed)
        e.after_query()
        return e.observations(observed)

    e.backend_port.query = search
    e.broker = RetrievalBroker(e.ingestion.reads, e.backend_port)
    e.query_request = RetrieveRepresentations(wire_version="1", retrieval_id="query1",
        generation=reference_to_wire(e.lease.attempt.generation), query=e.query_binding.reference,
        policy=policy_to_wire(QueryPolicy(2)))
    return e


def test_query_records_actual_provenance_scores_and_survives_backend_loss(query):
    e = query
    result = e.broker.retrieve(e.p, e.query_request)
    assert tuple(m.score for m in result.matches) == (8.0, 4.0)
    assert result.matches[0].binding == e.binding
    assert rows(e, "retrieval_queries") == rows(e, "retrieval_results") == 1
    assert e.search_calls[0][1][0] == point_id(e.binding)
    e.backend_port.query = lambda *args: pytest.fail("historical replay must not contact backend")
    assert RetrievalBroker(e.ingestion.reads, e.backend_port).retrieve(e.p, e.query_request) == result
    assert e.broker.read(e.p, "query1") == result
    with pytest.raises(RetrievalError, match="query_conflict"):
        e.broker.retrieve(e.p, e.query_request.model_copy(update={"policy": policy_to_wire(QueryPolicy(1))}))
    revoke(e)
    with pytest.raises(RightsError, match="rights_revoked"):
        e.broker.read(e.p, "query1")
    assert rows(e, "retrieval_results") == 1


def test_denied_targets_are_filtered_without_ids_scores_or_counts(query):
    e = query
    revoke(e)
    result = e.broker.retrieve(e.p, e.query_request)
    assert result.matches == () and e.search_calls == []
    raw = result.model_dump_json()
    assert e.binding.reference.binding_id not in raw
    assert 'omitted_count' not in raw and 'eligible_count' not in raw
    assert e.broker.read(e.p, "query1") == result


def test_revocation_during_backend_call_retains_intent_without_result(query):
    e = query
    e.after_query = lambda: revoke(e)
    with pytest.raises(RetrievalError, match="rights_changed"):
        e.broker.retrieve(e.p, e.query_request)
    assert rows(e, "retrieval_queries") == 1 and rows(e, "retrieval_results") == 0
    with pytest.raises(RetrievalError, match="query_pending"):
        e.broker.read(e.p, "query1")
    e.after_query = lambda: None
    result = e.broker.retrieve(e.p, e.query_request)
    assert result.matches == ()


def test_allowed_policy_revision_change_still_invalidates_observed_selection(query):
    e = query
    def change():
        rights = SourceRights(e.engine)
        old = rights.history(e.p, e.source.rights.rights_id, 1)
        rights.publish(e.p, old.model_copy(update={"reference": old.reference.model_copy(update={"revision":2}), "supersedes":old.reference}))
    e.after_query = change
    with pytest.raises(RetrievalError, match="rights_changed"):
        e.broker.retrieve(e.p, e.query_request)
    assert rows(e, "retrieval_results") == 0


@pytest.mark.parametrize("mutation,code", [
    (lambda observed: observed[:-1], "scores_incomplete"),
    (lambda observed: observed + (observed[0],), "score_duplicate"),
    (lambda observed: (SimpleNamespace(point=replace(observed[0].point, values=(0.0,)*16), score=3),), "query_content"),
    (lambda observed: (SimpleNamespace(point=observed[0].point, score=float('nan')),), "score_finite"),
    (lambda observed: [*observed], "query_response"),
    (lambda observed: (None,), "query_point"),
])
def test_backend_corruption_is_not_a_scientific_negative(query, mutation, code):
    e = query
    e.observations = mutation
    with pytest.raises(RetrievalError, match=code):
        e.broker.retrieve(e.p, e.query_request)
    assert rows(e, "retrieval_queries") == 1 and rows(e, "retrieval_results") == 0


def test_uncertain_backend_is_recoverable_and_cannot_publish_empty_result(query):
    e = query
    search = e.backend_port.query
    def unavailable(*args):
        raise TimeoutError("test-only unavailable backend")
    e.backend_port.query = unavailable
    with pytest.raises(TimeoutError):
        e.broker.retrieve(e.p, e.query_request)
    assert rows(e, "retrieval_results") == 0
    e.backend_port.query = search
    assert len(e.broker.retrieve(e.p, e.query_request).matches) == 2


def test_concurrent_same_request_converges_and_service_cannot_mutate_history(query):
    e = query
    barrier = Barrier(3)
    e.after_query = lambda: barrier.wait(timeout=10)
    with ThreadPoolExecutor(max_workers=3) as pool:
        values = list(pool.map(lambda _:e.broker.retrieve(e.p,e.query_request), range(3)))
    assert all(value == values[0] for value in values)
    assert rows(e, "retrieval_queries") == rows(e, "retrieval_results") == 1
    for table in ("retrieval_queries", "retrieval_results"):
        for operation in ("UPDATE artifacts."+table+" SET actor_id=actor_id", "DELETE FROM artifacts."+table):
            with pytest.raises(ProgrammingError), e.engine.begin() as c:
                c.execute(text(operation+" WHERE tenant_id=:tenant AND project_id=:project"),e.p.bindings)


def test_scope_actor_missing_and_unpublished_generation_never_admit(query):
    e = query
    with pytest.raises(RetrievalError, match="query_missing"):
        e.broker.read(e.p,"unknown")
    for principal in (replace(e.p,actor_id="other"), replace(e.p,scope=e.p.scope.model_copy(update={"project_id":"other"}))):
        with pytest.raises(RetrievalError, match="generation_missing"):
            e.broker.retrieve(principal,e.query_request)
    request=e.request.model_copy(update={"generation_id":"unpublished", "expected_head":e.query_request.generation})
    status=e.intents.prepare(e.p,request)
    with pytest.raises(RetrievalError, match="generation_unpublished"):
        e.broker.retrieve(e.p,e.query_request.model_copy(update={"generation":status.generation.reference}))
    assert rows(e,"retrieval_queries")==0


def test_query_source_process_rights_and_replay_read_rights_are_separate(query):
    e = query
    original = e.broker.retrieve(e.p, e.query_request)
    rights = SourceRights(e.engine)
    old = rights.history(e.p, "query-rights", 1)
    read_only = old.model_copy(update={"reference": old.reference.model_copy(update={"revision":2}),
        "supersedes":old.reference,"allowed_uses":("read",)})
    rights.publish(e.p,read_only)
    assert e.broker.retrieve(e.p,e.query_request)==original
    with pytest.raises(RightsError,match="rights_use_denied"):
        e.broker.retrieve(e.p,e.query_request.model_copy(update={"retrieval_id":"new-query"}))
    assert rows(e,"retrieval_queries")==1
    rights.publish(e.p,read_only.model_copy(update={"reference":read_only.reference.model_copy(update={"revision":3}),
        "supersedes":read_only.reference,"status":"revoked","allowed_uses":()}))
    with pytest.raises(RightsError,match="rights_revoked"):
        e.broker.retrieve(e.p,e.query_request)


def test_missing_rights_state_fails_instead_of_becoming_filtered_science(query,monkeypatch):
    e=query
    original=SourceRights.authorize
    def broken(self,connection,principal,artifacts=(),declared=(),use="read"):
        if artifacts==(e.binding.vector.artifact_id,):
            raise RightsError("rights_unavailable")
        return original(self,connection,principal,artifacts,declared,use)
    monkeypatch.setattr(SourceRights,"authorize",broken)
    with pytest.raises(RightsError,match="rights_unavailable"):
        e.broker.retrieve(e.p,e.query_request)
    assert rows(e,"retrieval_queries")==0 and not e.search_calls


def test_backend_profile_mismatch_and_forged_query_do_not_admit(query):
    e=query
    correct=e.backend_port.reference
    e.backend_port.reference=correct.model_copy(update={"sha256":"0"*64})
    with pytest.raises(RetrievalError,match="backend_profile"):
        e.broker.retrieve(e.p,e.query_request)
    e.backend_port.reference=correct
    for ref,code in ((e.query_request.query.model_copy(update={"binding_id":"unknown"}),"binding_missing"),
        (e.query_request.query.model_copy(update={"scope":e.p.scope.model_copy(update={"project_id":"other"})}),"binding_missing"),
        (e.query_request.query.model_copy(update={"sha256":"0"*64}),"query_binding")):
        with pytest.raises(RetrievalError,match=code):
            e.broker.retrieve(e.p,e.query_request.model_copy(update={"query":ref}))
    assert rows(e,"retrieval_queries")==0


def test_explicit_filter_roundtrip_is_set_canonical(query):
    e=query
    refs=e.request.bindings
    first=e.query_request.model_copy(update={"policy":policy_to_wire(QueryPolicy(2,refs))})
    value=e.broker.retrieve(e.p,first)
    # Construct the inbound DTO order explicitly; owner canonicalizes it.
    reverse=first.model_copy(update={"policy":first.policy.model_copy(update={"bindings":tuple(reversed(refs))})})
    assert e.broker.retrieve(e.p,reverse)==value
    empty=e.query_request.model_copy(update={"retrieval_id":"empty","policy":policy_to_wire(QueryPolicy(2,()))})
    assert e.broker.retrieve(e.p,empty).matches==()


def test_partial_rights_filter_reaches_backend_as_exact_allowed_ids(query):
    e=query
    generation_request=e.request.model_copy(update={"generation_id":"mixed", "expected_head":e.query_request.generation,
        "bindings":(e.binding.reference,e.query_binding.reference)})
    e.intents.prepare(e.p,generation_request)
    lease=e.leases.claim(e.p,"corpus","mixed")
    e.publication.build_and_verify(e.p,lease)
    status=e.publication.publish(e.p,lease)
    revoke(e)
    request=e.query_request.model_copy(update={"generation":status.generation.reference})
    result=e.broker.retrieve(e.p,request)
    assert e.search_calls==[(lease.attempt.namespace,(point_id(e.query_binding),))]
    assert len(result.matches)==1 and result.matches[0].binding==e.query_binding
    assert result.matches[0].score==8.0
    assert e.binding.reference.binding_id not in result.model_dump_json()
