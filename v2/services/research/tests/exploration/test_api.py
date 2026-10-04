"""Actual retained Research owner reads; scientific fixtures remain synthetic."""

import pytest
from amphora_contracts_research import (
    MissingMeasurement,
)
from amphora_research.observations.store import ObservationStore
from amphora_research.transport.host import ResearchHost
from fastapi.testclient import TestClient

from ..scientific_api.test_routes import configuration, secrets

pytestmark = pytest.mark.postgres


@pytest.fixture
def api(prepared, monkeypatch):
    case = prepared
    secrets(monkeypatch, case.engine)
    config = configuration(case.scope, ["read_scientific_record"])
    for label, scope, actions in (
        ("denied", case.scope, ["read_scientific_impact"]),
        (
            "foreign",
            case.scope.model_copy(update={"project_id": "foreign"}),
            ["read_scientific_record"],
        ),
    ):
        monkeypatch.setenv(label.upper() + "_TOKEN", label[0] * 32)
        config["principals"].append(
            {
                "token_env": label.upper() + "_TOKEN",
                "actor_id": label,
                "scope": scope.model_dump(mode="json"),
                "actions": actions,
            }
        )
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            client.headers["Authorization"] = "Bearer " + "s" * 32
            yield case, client
    finally:
        host.close()


def queries(case):
    experiment = case.plan.reference.model_dump(mode="json")
    return {
        "catalog": experiment,
        "specimens": {"wire_version": "1", "experiment": experiment, "limit": 1},
        "properties": {
            "wire_version": "1",
            "experiment": experiment,
            "observations": [
                case.first.reference.model_dump(mode="json"),
                case.second.reference.model_dump(mode="json"),
            ],
            "limit": 1,
        },
        "observation-series": {
            "wire_version": "1",
            "observation": case.second.reference.model_dump(mode="json"),
            "limit": 1,
        },
    }


def test_authenticated_bounded_routes_and_scope_checks(api):
    case, client = api
    for suffix, query in queries(case).items():
        path = "/v1/research-explore/" + suffix
        result = client.post(path, json=query)
        assert (
            result.status_code == 200 and result.headers["cache-control"] == "no-store"
        )
        assert len(result.content) <= 1048576
        for token, status in (("d", 403), ("f", 403), ("x", 401)):
            assert (
                client.post(
                    path, json=query, headers={"Authorization": "Bearer " + token * 32}
                ).status_code
                == status
            )
        assert (
            client.post(path, json={**query, "authority": "accepted"}).status_code
            == 422
        )
        assert (
            client.post(
                path,
                content=b" " * 262145,
                headers={"Content-Type": "application/json"},
            ).status_code
            == 413
        )
        missing = dict(query)
        key = "observation" if suffix == "observation-series" else "experiment"
        if suffix == "catalog":
            missing["revision"] = 99
        else:
            missing[key] = {**query[key], "revision": 99}
        assert client.post(path, json=missing).status_code == 404


def test_selected_existence_checked_before_loading_only_the_page(api, monkeypatch):
    case, client = api
    query = queries(case)["properties"]
    original = ObservationStore.read
    read = []

    def observed(store, scope, reference):
        read.append(reference)
        return original(store, scope, reference)

    monkeypatch.setattr(ObservationStore, "read", observed)
    missing = {
        **query,
        "observations": [
            query["observations"][0],
            {**query["observations"][1], "revision": 99},
        ],
    }
    assert (
        client.post("/v1/research-explore/properties", json=missing).status_code == 404
    )
    assert read == []
    first = client.post("/v1/research-explore/properties", json=query).json()
    assert read == [case.first.reference]
    next_query = {**query, "position": first["next_position"]}
    second = client.post("/v1/research-explore/properties", json=next_query).json()
    assert read == [case.first.reference, case.second.reference]
    assert second["rows"][0]["value"]["kind"] == "series"
    assert second["rows"][0]["value"]["point_count"] == 2
    assert second["next_position"] is None
    corrected = case.first.model_copy(
        update={
            "reference": case.first.reference.model_copy(update={"revision": 2}),
            "supersedes": case.first.reference,
            "value": MissingMeasurement(kind="missing", reason="corrected_report"),
        }
    )
    case.store.publish(case.scope, "fixture", corrected)
    assert client.post("/v1/research-explore/properties", json=query).json() == first
    changed = {
        **query,
        "observations": [
            corrected.reference.model_dump(mode="json"),
            query["observations"][1],
        ],
    }
    assert (
        client.post("/v1/research-explore/properties", json=changed).json()["rows"][0][
            "value"
        ]["kind"]
        == "missing"
    )
    response = client.post(
        "/v1/research-explore/properties",
        json={**changed, "position": first["next_position"]},
    )
    assert (
        response.status_code == 409 and response.json()["code"] == "view_position_query"
    )


def test_series_preserves_equal_x_and_scalar_conflict(api):
    case, client = api
    query = queries(case)["observation-series"]
    path = "/v1/research-explore/observation-series"
    first = client.post(path, json=query).json()
    second = client.post(
        path, json={**query, "position": first["next_position"]}
    ).json()
    assert first["points"][0]["x"] == second["points"][0]["x"]
    assert second["points"][0]["y"]["kind"] == "missing"
    response = client.post(
        path,
        json={**query, "observation": case.first.reference.model_dump(mode="json")},
    )
    assert response.status_code == 409 and response.json()["code"] == "view_not_series"


@pytest.mark.parametrize("fault", ["missing", "wrong_reference", "invalid_value"])
def test_stored_record_faults_are_owner_failures_not_missing_science(
    api, monkeypatch, fault
):
    case, client = api
    record = (
        None
        if fault == "missing"
        else case.first.model_copy(update={"reference": case.second.reference})
        if fault == "wrong_reference"
        else case.first.model_copy(
            update={
                "value": case.first.value.model_copy(
                    update={
                        "quantity": case.first.value.quantity.model_copy(
                            update={"value": "1e129"}
                        )
                    }
                )
            }
        )
    )
    monkeypatch.setattr(ObservationStore, "read", lambda *args: record)
    response = client.post(
        "/v1/research-explore/properties", json=queries(case)["properties"]
    )
    assert response.status_code == 503
    assert response.json() == {"code": "scientific_owner_unavailable"}
