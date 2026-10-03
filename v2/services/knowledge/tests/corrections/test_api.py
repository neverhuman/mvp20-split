"""Scoped Knowledge correction routes over actual owner PostgreSQL."""
from dataclasses import replace

import pytest
from amphora_contracts_graph_runtime import ReceiptCorrectionView
from amphora_knowledge.transport.api import create_app
from amphora_knowledge.transport.credentials import Credentials
from fastapi.testclient import TestClient

pytestmark = pytest.mark.postgres
HEADERS = {"Authorization":"Bearer " + "c"*32}


def test_reference_selection_and_correction_grants_are_separate(correction_case):
    c = correction_case
    reader = replace(c.principal, actions=frozenset({"select_reasoning_receipt"}))
    credentials = Credentials([
        ("c"*32,c.correction_principal), ("r"*32,reader),
        ("f"*32,replace(reader,scope=reader.scope.model_copy(update={"project_id":"foreign"}))),
        ("x"*32,replace(c.correction_principal,actor_id="other"))])
    body = c.command.model_dump(mode="json")
    query = {"wire_version":"1","chain":body["chain"],"revision":None}
    with TestClient(create_app(c.authoring,credentials,publication=c.publishing)) as api:
        assert api.post("/v1/reasoning-receipts/correct",json=body).status_code == 401
        assert api.post("/v1/reasoning-receipts/correct",json=body,headers={"Authorization":"Bearer " + "r"*32}).status_code == 403
        response = api.post("/v1/reasoning-receipts/correct",json=body,headers=HEADERS)
        assert response.status_code == 200
        view = ReceiptCorrectionView.model_validate(response.json())
        assert view.record.receipt.outcome.status == "accepted"
        assert api.post("/v1/reasoning-receipts/correct",json=body,headers=HEADERS).json() == response.json()
        assert api.post("/v1/reasoning-publications/read",json=body["source"],headers=HEADERS).status_code == 403
        assert api.post("/v1/reasoning-receipts/select",json=query,headers=HEADERS).status_code == 403
        for reference in (None,response.json()["reference"]):
            selected = api.post("/v1/reasoning-receipts/select",json=query | {"revision":reference},headers={"Authorization":"Bearer " + "r"*32})
            assert selected.status_code == 200 and selected.json() == response.json()
            assert selected.headers["cache-control"] == "no-store"
        assert api.post("/v1/reasoning-receipts/select",json=query,headers={"Authorization":"Bearer " + "f"*32}).status_code == 403
        assert api.post("/v1/reasoning-receipts/correct",json=body,headers={"Authorization":"Bearer " + "x"*32}).status_code == 403
        assert api.post("/v1/reasoning-receipts/correct",json=body | {"reason_code":"changed"},headers=HEADERS).status_code == 409
        assert api.post("/v1/reasoning-receipts/correct",json=body | {"source_receipt":{}},headers=HEADERS).status_code == 422
        query["chain"]["chain_id"] = "absent"
        assert api.post("/v1/reasoning-receipts/select",json=query,headers={"Authorization":"Bearer " + "r"*32}).status_code == 404
