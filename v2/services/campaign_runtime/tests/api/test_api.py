import copy
import json

from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.graph import Graph
from amphora_contracts_campaigns import CampaignDefinition
from export_schemas import ROOT
from fastapi.testclient import TestClient

CASES = json.loads(
    (ROOT / "contracts/fixtures/v1/wire_cases.json").read_text()
)


def fixture(name):
    return copy.deepcopy(next(c["payload"] for c in CASES if c["name"] == name))


def issues(payload):
    dto = CampaignDefinition.model_validate_json(json.dumps(payload))
    return {i.code for i in Graph.from_contract(dto.body).issues()}


def test_api_reports_validation_only_and_never_creates_a_run():
    with TestClient(create_app()) as client:
        assert client.get("/health").json()["execution_available"] is False
        response = client.post("/v1/campaign-definitions/validate", json=fixture("valid-campaign"))
        assert response.status_code == 200, response.text
        assert response.json()["structurally_valid"] is True
        assert response.json()["executable"] is False
        assert client.post("/v1/runs", json={}).status_code == 404
        schema = client.get("/openapi.json").json()
        assert "CampaignDefinition" in schema["components"]["schemas"]

        def walk(value):
            if isinstance(value, dict):
                if "$ref" in value:
                    assert value["$ref"].startswith("#/components/schemas/")
                    assert value["$ref"].split("/")[-1] in schema["components"]["schemas"]
                for item in value.values():
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(schema)


def test_api_bounds_and_redacts_validation_errors():
    with TestClient(create_app()) as client:
        raw = fixture("valid-campaign")
        raw["private_secret"] = "do-not-echo-this"
        response = client.post("/v1/campaign-definitions/validate", json=raw)
        assert response.status_code == 422
        assert "do-not-echo-this" not in response.text
        assert client.post("/v1/campaign-definitions/validate", content=b"x" * 262145).status_code == 413
        assert client.post("/v1/campaign-definitions/validate", content=b"{").status_code == 422
