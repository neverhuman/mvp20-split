"""Optional HTTP over actual owner state, with test-only backend observations."""

import asyncio
from dataclasses import replace

import httpx
import pytest
from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.api import create_app
from amphora_data_artifacts.retrieval.qdrant.transport import QdrantError
from amphora_data_artifacts.retrieval.service import RetrievalService
from fastapi.testclient import TestClient
from sqlalchemy import text

from .queries.test_broker import query as query
from .test_generation_publication import revoke, rows

pytestmark = pytest.mark.postgres
BASE = "/v1/retrieval"


@pytest.fixture
def http(query):
    e = query
    e.service = RetrievalService(e.ingestion.reads, e.backend_port)
    credentials = Credentials(
        [
            ("a" * 32, e.p),
            ("r" * 32, replace(e.p, actions=frozenset({"representation_read", "read"}))),
            ("n" * 32, replace(e.p, actions=frozenset({"read"}))),
            ("f" * 32, replace(e.p, scope=e.p.scope.model_copy(update={"project_id": "foreign"}))),
        ]
    )
    e.app = create_app(e.ingestion.env.uploads, e.ingestion.env.storage, credentials, retrieval=e.service)
    e.headers = {"Authorization": "Bearer " + "a" * 32}
    with TestClient(e.app) as client:
        e.client = client
        yield e


def test_authentication_and_actions_precede_bounded_json(http):
    e = http
    for path in ("/generations", "/queries"):
        assert e.client.post(BASE + path, content=b"invalid").status_code == 401
        assert (
            e.client.post(
                BASE + path, content=b"invalid", headers={"Authorization": "Bearer " + "n" * 32}
            ).status_code
            == 403
        )
        assert e.client.post(BASE + path, content=b"{}", headers=e.headers).status_code == 415
        headers = e.headers | {"Content-Type": "application/json"}
        for raw in (
            b"{}",
            b'{"x":1,"x":2}',
            b'{"x":NaN}',
            b'{"x":1e999}',
            b'{"x":' + b"[" * 70 + b"0" + b"]" * 70 + b"}",
        ):
            assert e.client.post(BASE + path, content=raw, headers=headers).status_code == 422
        assert (
            e.client.post(BASE + path, content=b" " * (4 * 1024 * 1024 + 1), headers=headers).status_code
            == 413
        )
    assert rows(e, "retrieval_queries") == 0


def test_generation_advance_digest_read_and_busy_recovery(http):
    e = http
    request = e.request.model_copy(
        update={"generation_id": "g2", "expected_head": e.query_request.generation}
    )
    e.intents.prepare(e.p, request)
    e.leases.claim(e.p, "corpus", "g2")
    response = e.client.post(BASE + "/generations", headers=e.headers, json=request.model_dump(mode="json"))
    assert response.status_code == 202 and response.json()["state"] == "building"
    route = BASE + "/generations/corpus/g2"
    digest = response.json()["generation"]["reference"]["sha256"]
    assert e.client.get(route, headers=e.headers, params={"sha256": digest}).json() == response.json()
    assert e.client.get(route, headers=e.headers, params={"sha256": "0" * 64}).status_code == 409
    assert e.client.get(route, headers=e.headers).status_code == 422
    with e.engine.begin() as c:
        c.execute(
            text(
                "UPDATE artifacts.index_generation_cursors SET expires_at=clock_timestamp()-interval '1 second' "
                "WHERE tenant_id=:tenant AND project_id=:project AND generation_id='g2'"
            ),
            e.p.bindings,
        )
    result = e.client.post(BASE + "/generations", headers=e.headers, json=request.model_dump(mode="json"))
    assert result.status_code == 200 and result.json()["state"] == "published"
    assert result.headers["Cache-Control"] == "no-store"
    assert (
        e.client.post(BASE + "/generations", headers=e.headers, json=request.model_dump(mode="json")).json()
        == result.json()
    )
    assert (
        e.client.get(
            route, params={"sha256": digest}, headers={"Authorization": "Bearer " + "f" * 32}
        ).status_code
        == 404
    )


def test_query_http_replay_current_rights_and_pending_operational_error(http):
    e = http
    request = e.query_request.model_dump(mode="json")
    response = e.client.post(BASE + "/queries", headers=e.headers, json=request)
    assert response.status_code == 200 and [m["score"] for m in response.json()["matches"]] == [8.0, 4.0]
    assert response.headers["Cache-Control"] == "no-store"
    assert e.client.get(BASE + "/queries/query1", headers=e.headers).json() == response.json()
    assert e.client.get(BASE + "/queries/absent", headers=e.headers).status_code == 404

    def unavailable(*args):
        raise QdrantError("qdrant_unavailable")

    e.backend_port.query = unavailable
    assert e.client.post(BASE + "/queries", headers=e.headers, json=request).json() == response.json()
    request["retrieval_id"] = "pending"
    result = e.client.post(BASE + "/queries", headers=e.headers, json=request)
    assert result.status_code == 503 and result.json()["detail"] == "qdrant_unavailable"
    assert e.client.get(BASE + "/queries/pending", headers=e.headers).status_code == 409
    revoke(e)
    result = e.client.get(BASE + "/queries/query1", headers=e.headers)
    assert result.status_code == 403 and result.json()["detail"] == "rights_revoked"
    assert rows(e, "retrieval_results") == 1


def test_profile_lookup_failure_is_explicit_and_routes_are_opt_in(http):
    e = http
    request = e.request.model_dump(mode="json")
    request["generation_id"] = "unknown-profile"
    request["profile"]["profile_id"] = "unregistered"
    assert e.client.post(BASE + "/generations", headers=e.headers, json=request).status_code == 404
    app = create_app(e.ingestion.env.uploads, e.ingestion.env.storage, Credentials([("a" * 32, e.p)]))
    with TestClient(app) as client:
        assert client.post(BASE + "/generations", headers=e.headers, json=request).status_code == 404


def test_incomplete_body_hits_absolute_upload_deadline(http):
    e = http

    async def run():
        async def slow():
            yield b"{"
            await asyncio.sleep(6)
            yield b"}"

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=e.app), base_url="http://fixture"
        ) as client:
            result = await client.post(
                BASE + "/queries", headers=e.headers | {"Content-Type": "application/json"}, content=slow()
            )
            assert result.status_code == 408 and result.json()["detail"] == "request_incomplete"

    asyncio.run(run())
    assert rows(e, "retrieval_queries") == 0


def test_expired_verified_build_is_truthfully_terminal_without_republishing(http):
    e = http
    request = e.request.model_copy(
        update={"generation_id": "expired", "expected_head": e.query_request.generation}
    )
    e.intents.prepare(e.p, request)
    lease = e.leases.claim(e.p, "corpus", "expired")
    e.publication.build_and_verify(e.p, lease)
    with e.engine.begin() as c:
        c.execute(
            text(
                "UPDATE artifacts.index_generation_cursors SET expires_at=clock_timestamp()-interval '1 second' "
                "WHERE tenant_id=:tenant AND project_id=:project AND generation_id='expired'"
            ),
            e.p.bindings,
        )
    result = e.client.post(BASE + "/generations", headers=e.headers, json=request.model_dump(mode="json"))
    assert result.status_code == 200 and result.json()["state"] == "failed"
    assert rows(e, "index_publications") == 1
