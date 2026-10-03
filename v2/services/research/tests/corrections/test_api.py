"""Authenticated correction routes over the real Research owner store."""
import pytest
from amphora_contracts_graph_runtime import ReceiptCorrectionView
from amphora_research.persistence.ledger import IdentityLedger
from amphora_research.transport.access import Credentials, Principal
from amphora_research.transport.api import create_app
from amphora_research.transport.assessments import AssessmentOperations
from amphora_research.transport.resolver import IdentityResolver
from fastapi.testclient import TestClient

pytestmark = pytest.mark.postgres
HEADERS = {"Authorization":"Bearer " + "a"*32}


@pytest.fixture
def client(correction_case):
    store, request, actor = correction_case
    # Read/correction routes require no scientific profile or peer calls.
    operations = object.__new__(AssessmentOperations)
    operations.engine = store.engine
    grants = Credentials([
        ("a"*32, Principal(actor, request.chain.scope, frozenset({"correct_assessment_receipt", "select_assessment_receipt"}))),
        ("r"*32, Principal(actor, request.chain.scope, frozenset({"select_assessment_receipt"}))),
        ("x"*32, Principal("other", request.chain.scope, frozenset({"correct_assessment_receipt"}))),
        ("f"*32, Principal(actor, request.chain.scope.model_copy(update={"project_id":"foreign"}), frozenset({"select_assessment_receipt"})))])
    with TestClient(create_app(IdentityResolver(IdentityLedger(store.engine)), grants, operations)) as api:
        yield api, request


def test_correction_and_explicit_selection_require_separate_scoped_grants(client):
    api, request = client
    body = request.model_dump(mode="json")
    query = {"wire_version":"1", "chain":body["chain"], "revision":None}
    assert api.post("/v1/assessment-receipts/correct", json=body).status_code == 401
    assert api.post("/v1/assessment-receipts/correct", json=body, headers={"Authorization":"Bearer " + "r"*32}).status_code == 403
    response = api.post("/v1/assessment-receipts/correct", json=body, headers=HEADERS)
    assert response.status_code == 200
    first = ReceiptCorrectionView.model_validate(response.json())
    assert first.record.receipt.outcome.status == "abstained"
    assert api.post("/v1/assessment-receipts/correct", json=body, headers=HEADERS).json() == response.json()
    selected = api.post("/v1/assessment-receipts/select", json=query, headers={"Authorization":"Bearer " + "r"*32})
    assert selected.status_code == 200 and selected.json() == response.json()
    assert selected.headers["cache-control"] == "no-store"
    pinned = api.post("/v1/assessment-receipts/select", json=query | {"revision":response.json()["reference"]}, headers=HEADERS)
    assert pinned.status_code == 200 and pinned.json() == response.json()
    assert api.post("/v1/assessment-receipts/select", json=query, headers={"Authorization":"Bearer " + "f"*32}).status_code == 403
    assert api.post("/v1/assessment-receipts/correct", json=body, headers={"Authorization":"Bearer " + "x"*32}).status_code == 403
    assert api.post("/v1/assessment-receipts/correct", json=body | {"reason_code":"changed"}, headers=HEADERS).status_code == 409
    assert api.post("/v1/assessment-receipts/correct", json=body | {"change_id":"missing", "assessment_id":"missing"}, headers=HEADERS).status_code == 409
    assert api.post("/v1/assessment-receipts/correct", json=body | {"source_receipt":response.json()["record"]["receipt"]}, headers=HEADERS).status_code == 422
    query["chain"]["chain_id"] = "absent"
    assert api.post("/v1/assessment-receipts/select", json=query, headers=HEADERS).status_code == 404
