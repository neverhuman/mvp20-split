"""Actual owner SQL and production HTTP boundary; no source reads for projections."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_contracts_knowledge import CorrectAssertion
from amphora_knowledge.transport.api import create_app
from amphora_knowledge.transport.credentials import Credentials
from fastapi.testclient import TestClient

from ..persistence.test_ledger import observation

pytestmark = pytest.mark.postgres


@pytest.fixture
def api(stored_graph):
    case = stored_graph
    case.receipt = case.ledger.accept(
        case.principal, case.proposal, observation(case.proposal)
    )
    case.revision = case.receipt.decision.head.snapshot
    reader = replace(
        case.principal, actor_id="reader", actions=frozenset({"read_graph"})
    )
    denied = replace(reader, actions=frozenset({"propose_graph"}))
    foreign = replace(
        reader, scope=reader.scope.model_copy(update={"project_id": "other"})
    )
    credentials = Credentials(
        [("r" * 32, reader), ("d" * 32, denied), ("f" * 32, foreign)]
    )
    # Read-only route tests never call this workflow's submit operation.
    with TestClient(
        create_app(SimpleNamespace(ledger=case.ledger), credentials)
    ) as client:
        client.headers["Authorization"] = "Bearer " + "r" * 32
        yield case, client


def queries(case):
    revision = case.revision.model_dump(mode="json")
    entity = case.proposal.operations[0].entity.reference.model_dump(mode="json")
    return {
        "catalog": revision,
        "entities": {"wire_version": "1", "revision": revision, "limit": 1},
        "neighborhood": {"wire_version": "1", "revision": revision, "focus": entity},
        "object": {
            "wire_version": "1",
            "revision": revision,
            "selection": {"kind": "entity", "reference": entity},
        },
    }


def test_exact_read_routes_scope_grant_absence_and_bounded_request(api):
    case, client = api
    for route, query in queries(case).items():
        path = "/v1/graph-explore/" + route
        result = client.post(path, json=query)
        assert result.status_code == 200
        assert result.headers["cache-control"] == "no-store"
        assert len(result.content) <= 1048576
        for token, status in [("d", 403), ("f", 403), ("x", 401)]:
            assert (
                client.post(
                    path, json=query, headers={"Authorization": "Bearer " + token * 32}
                ).status_code
                == status
            )
        missing = dict(query)
        if route == "catalog":
            missing["sha256"] = "0" * 64
        else:
            missing["revision"] = dict(query["revision"], sha256="0" * 64)
        assert client.post(path, json=missing).status_code == 404
        assert (
            client.post(path, json={**query, "authority": "accepted"}).status_code
            == 422
        )
        assert (
            client.post(
                path, content=b" ", headers={"Content-Type": "text/plain"}
            ).status_code
            == 415
        )
        assert (
            client.post(
                path,
                content=b" " * 262145,
                headers={"Content-Type": "application/json"},
            ).status_code
            == 413
        )


def test_continuation_survives_new_head_but_cannot_switch_query_or_revision(api):
    case, client = api
    query = queries(case)["entities"]
    route = "/v1/graph-explore/entities"
    first = client.post(route, json=query).json()
    second_query = {**query, "position": first["next_position"]}
    original_second = client.post(route, json=second_query).json()
    old = case.proposal.operations[2].assertion
    corrected = old.model_copy(
        update={
            "reference": old.reference.model_copy(update={"revision": 2}),
            "supersedes": old.reference,
            "polarity": "negated",
        }
    )
    proposal = case.proposal.model_copy(
        update={
            "change_id": "correction",
            "base": case.receipt.decision.head,
            "operations": (
                CorrectAssertion(
                    operation="correct_assertion",
                    prior=old.reference,
                    replacement=corrected,
                ),
            ),
        }
    )
    receipt = case.ledger.accept(case.principal, proposal, observation(proposal))
    assert receipt.decision.outcome == "accepted"
    assert client.post(route, json=second_query).json() == original_second
    assert client.post(route, json=query).json() == first
    for changes in (
        {"text": "B"},
        {"revision": receipt.decision.head.snapshot.model_dump(mode="json")},
    ):
        result = client.post(route, json={**second_query, **changes})
        assert (
            result.status_code == 409
            and result.json()["code"] == "explore_position_query"
        )
    neighborhood = queries(case)["neighborhood"]
    original = client.post("/v1/graph-explore/neighborhood", json=neighborhood).json()
    successor = client.post(
        "/v1/graph-explore/neighborhood",
        json={
            **neighborhood,
            "revision": receipt.decision.head.snapshot.model_dump(mode="json"),
        },
    ).json()
    assert original["assertions"][0]["polarity"] == "affirmed"
    assert successor["assertions"][0]["polarity"] == "negated"


def test_missing_object_cross_graph_focus_and_bad_cursor_fail_without_fabrication(api):
    case, client = api
    query = queries(case)
    detail = query["object"]
    detail["selection"]["reference"]["entity_id"] = "missing"
    assert (
        client.post("/v1/graph-explore/object", json=detail).json()["code"]
        == "explore_entity_missing"
    )
    query["neighborhood"]["focus"]["graph"]["graph_id"] = "other"
    response = client.post("/v1/graph-explore/neighborhood", json=query["neighborhood"])
    assert (
        response.status_code == 409 and response.json()["code"] == "explore_focus_graph"
    )


def test_corrupt_snapshot_adapter_output_is_hidden_as_owner_failure(api, monkeypatch):
    # Fault injection after the actual persisted read; no database corruption or repair.
    case, client = api
    original = case.ledger.snapshot(case.principal, case.revision)
    malformed = original.model_copy(
        update={"reference": original.reference.model_copy(update={"sha256": "0" * 64})}
    )
    monkeypatch.setattr(case.ledger, "snapshot", lambda principal, reference: malformed)
    response = client.post("/v1/graph-explore/catalog", json=queries(case)["catalog"])
    assert response.status_code == 503
    assert response.json() == {"code": "knowledge_owner_unavailable"}
