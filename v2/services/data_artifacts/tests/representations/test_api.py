"""Opt-in HTTP boundary over actual Data/PG state, not an installed-process acceptance claim."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.api import create_app
from amphora_data_artifacts.representations.bindings.workflow import RecoveryBudget
from amphora_data_artifacts.representations.service import RepresentationService
from fastapi.testclient import TestClient

pytestmark = pytest.mark.postgres
BASE = "/v1/representations"


@pytest.fixture
def http(flow):
    e = flow
    service = RepresentationService(e.e.e.reads, e.uploads, e.storage)
    principals = [
        e.p,
        replace(e.p, actions=frozenset({"representation_read", "read"})),
        replace(e.p, scope=e.p.scope.model_copy(update={"project_id": "outside"})),
        replace(e.p, actor_id="other"),
    ]
    credentials = Credentials(
        [(letter * 32, principal) for letter, principal in zip("rvwa", principals, strict=True)]
    )
    app = create_app(e.uploads, e.storage, credentials, representations=service)
    with TestClient(app) as client:
        yield SimpleNamespace(
            e=e, service=service, client=client, headers={"Authorization": "Bearer " + "r" * 32}
        )


def test_profile_discovery_registration_and_exact_digest_scoping(http):
    h = http
    response = h.client.get(BASE + "/available-profiles", headers=h.headers)
    assert response.status_code == 200 and response.headers["Cache-Control"] == "no-store"
    profiles = response.json()
    assert len(profiles) == 1
    result = h.client.post(BASE + "/profiles", json=profiles[0], headers=h.headers)
    assert result.status_code == 200
    ref = result.json()
    route = BASE + "/profiles/" + ref["profile_id"] + "/" + ref["version"]
    assert h.client.get(route, params={"sha256": ref["sha256"]}, headers=h.headers).json() == profiles[0]
    assert h.client.get(route, params={"sha256": "a" * 64}, headers=h.headers).status_code == 409
    assert h.client.get(route, headers=h.headers).status_code == 422
    other = {"Authorization": "Bearer " + "w" * 32}
    assert h.client.get(route, params={"sha256": ref["sha256"]}, headers=other).status_code == 404
    changed = dict(profiles[0], limitations=["conflicting immutable meaning"])
    assert h.client.post(BASE + "/profiles", json=changed, headers=h.headers).status_code == 409


def test_authentication_and_grants_precede_body_parsing(http):
    h = http
    for route in ("/profiles", "/encodings"):
        assert h.client.post(BASE + route, content=b"not json").status_code == 401
        response = h.client.post(
            BASE + route, content=b"not json", headers={"Authorization": "Bearer " + "v" * 32}
        )
        assert response.status_code == 403
    headers = h.headers | {"Content-Type": "application/json"}
    for payload in (b'{"wire_version":"1","wire_version":"1"}', b'{"value":NaN}', b"{}"):
        assert h.client.post(BASE + "/encodings", content=payload, headers=headers).status_code == 422
    assert h.client.post(BASE + "/encodings", content=b"x" * 65537, headers=headers).status_code == 413
    assert h.client.post(BASE + "/encodings", content=b"{}", headers=h.headers).status_code == 415
    assert h.service.workflow.requests.read(h.e.p, h.e.request.encoding_id) is None


def test_pending_status_is_read_only_then_post_publishes_and_other_actor_reads_binding(http):
    h = http
    h.service.workflow.budget = RecoveryBudget(1)
    response = h.client.post(BASE + "/encodings", json=h.e.request.model_dump(mode="json"), headers=h.headers)
    assert response.status_code == 202 and response.json()["outcome"]["state"] == "pending"
    route = BASE + "/encodings/" + h.e.request.encoding_id
    assert h.client.get(route, headers=h.headers).json() == response.json()
    assert h.client.get(route, headers={"Authorization": "Bearer " + "a" * 32}).status_code == 404
    h.service.workflow.budget = RecoveryBudget()
    response = h.client.post(BASE + "/encodings", json=h.e.request.model_dump(mode="json"), headers=h.headers)
    assert response.status_code == 200
    binding = response.json()["outcome"]["binding"]
    binding_route = BASE + "/bindings/" + binding["reference"]["binding_id"]
    assert h.client.get(binding_route, headers={"Authorization": "Bearer " + "a" * 32}).json() == binding
    assert h.client.get(binding_route, headers={"Authorization": "Bearer " + "w" * 32}).status_code == 404
    assert h.client.get(BASE + "/bindings/missing", headers=h.headers).status_code == 404


def test_current_binding_rights_are_distinct_from_original_encoding_status(http):
    h = http
    published = h.client.post(
        BASE + "/encodings", json=h.e.request.model_dump(mode="json"), headers=h.headers
    )
    assert published.status_code == 200
    binding = published.json()["outcome"]["binding"]
    rights = h.e.e.e.workflow.rights
    prior = rights.history(h.e.p, h.e.e.source.rights.rights_id, 1)
    denied = prior.model_copy(
        update={
            "reference": prior.reference.model_copy(update={"revision": 2}),
            "supersedes": prior.reference,
            "status": "revoked",
            "allowed_uses": (),
        }
    )
    rights.publish(h.e.p, denied)
    response = h.client.get(BASE + "/bindings/" + binding["reference"]["binding_id"], headers=h.headers)
    assert response.status_code == 403 and response.json()["reason_code"] == "rights_revoked"
    assert (
        h.client.get(BASE + "/encodings/" + h.e.request.encoding_id, headers=h.headers).json()
        == published.json()
    )
    assert (
        h.client.post(BASE + "/encodings", json=h.e.request.model_dump(mode="json"), headers=h.headers).json()
        == published.json()
    )
    alias = h.e.request.model_copy(update={"encoding_id": "new"})
    assert (
        h.client.post(BASE + "/encodings", json=alias.model_dump(mode="json"), headers=h.headers).status_code
        == 403
    )


def test_registered_profile_does_not_install_encoder_code(http):
    h = http
    profile = h.client.get(BASE + "/available-profiles", headers=h.headers).json()[0]
    profile["profile_id"] = "unreviewed"
    profile["encoder"]["provider"] = "unreviewed-provider"
    response = h.client.post(BASE + "/profiles", json=profile, headers=h.headers)
    assert response.status_code == 200
    request = h.e.request.model_dump(mode="json")
    request["profile"] = response.json()
    response = h.client.post(BASE + "/encodings", json=request, headers=h.headers)
    assert response.status_code == 422
    assert response.json()["detail"] == "representation_encoder_unavailable"


def test_bad_source_span_reports_conflict_without_registering_intent(http):
    h = http
    body = h.e.request.model_dump(mode="json")
    body["source"]["sha256"] = "0" * 64
    response = h.client.post(BASE + "/encodings", json=body, headers=h.headers)
    assert response.status_code == 409
    assert h.service.workflow.requests.read(h.e.p, h.e.request.encoding_id) is None


def test_slow_request_body_has_a_real_deadline_before_any_intent(http):
    import asyncio

    from amphora_data_artifacts.access import Credentials
    from amphora_data_artifacts.representations.api import representation_router
    from fastapi import HTTPException, Request, Response

    h = http
    router = representation_router(h.service, Credentials([("r" * 32, h.e.p)]))
    endpoint = next(
        route.endpoint
        for route in router.routes
        if route.path == BASE + "/encodings" and "POST" in route.methods
    )

    async def slow():
        await asyncio.sleep(6)
        return {"type": "http.request", "body": b"{}", "more_body": False}

    request = Request(
        {
            "type": "http",
            "headers": [
                (b"authorization", ("Bearer " + "r" * 32).encode()),
                (b"content-type", b"application/json"),
            ],
        },
        receive=slow,
    )
    with pytest.raises(HTTPException) as failure:
        asyncio.run(endpoint(request, Response()))
    assert failure.value.status_code == 408
    assert h.service.workflow.requests.read(h.e.p, h.e.request.encoding_id) is None
