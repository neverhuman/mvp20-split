"""Numeric profile through actual owner HTTP/transactions and process replacement."""

import json
import sys
from dataclasses import replace

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_campaign_runtime.definitions.admission import DraftAdmissionGuard
from amphora_campaign_runtime.definitions.validation import ValidationUniverse
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_contracts_commands import NUMERIC_ENCODING
from amphora_contracts_graph_runtime import parse_graph_command
from fastapi.testclient import TestClient
from sqlalchemy import text

from ..acceptance.paired_support import Process, decoded, free_port, isolated_env, request
from ..scheduling.test_graph_host import graph_host
from .test_commands import bindings, command


def numeric_save(e, value=1.25):
    envelope = json.loads(command(e).canonical_bytes)
    envelope["encoding"] = NUMERIC_ENCODING
    number_type = {"kind": "scalar", "scalar": "number", "unit": "1"}
    envelope["payload"]["definition"]["body"] = {
        "inputs": [{"name": "supplied", "value_type": number_type}],
        "outputs": [{"name": name, "value_type": number_type} for name in ("literal", "supplied")],
        "nodes": [{"kind": "finish", "node_id": "done", "outputs": [
            {"port": "literal", "source": {"kind": "number", "value": value, "unit": "1"}},
            {"port": "supplied", "source": {"kind": "input", "name": "supplied"}}]}]}
    return envelope


@pytest.mark.parametrize("value", [1, 1.25, 1e20])
def test_numeric_save_validate_admit_and_receipt_replay(fixture_env, value):
    e = fixture_env
    e.principal = replace(e.principal, actions=e.principal.actions | {"author", "validate", "read", "maintain"})
    universe = ValidationUniverse(e.principal.scope, (), ())
    universes = {(e.principal.scope.tenant_id, e.principal.scope.project_id): universe}
    admission = GraphAdmission(e.engine, PlanCatalog([]), bindings_enabled=True, drafts=DraftAdmissionGuard(e.engine, universes))
    credentials = RuntimeCredentials([("n" * 32, e.principal)])
    headers = {"Authorization": "Bearer " + "n" * 32}
    app = create_app(e.service, credentials, graphs=(admission, GraphAdvancer(e.engine)), authoring=True, universes=universes)
    saved_request = numeric_save(e, value)
    with TestClient(app) as client:
        response = client.post("/v1/definition-drafts/save", json=saved_request, headers=headers)
        response.raise_for_status()
        saved = response.json()
        assert saved["outcome"]["status"] == "accepted"
        original = client.get("/v1/definition-drafts/draft", headers=headers).json()
        assert original["definition"]["body"]["nodes"][0]["outputs"][0]["source"]["value"] == value
        validate = {"identity": {**saved_request["identity"], "command_family": "definition.validate", "command_id": "validate"},
            "payload": {"draft_id": "draft", "revision": 1, "content_sha256": original["head"]["content_sha256"]}}
        receipt = client.post("/v1/definition-drafts/validate", json=validate, headers=headers)
        receipt.raise_for_status()
        result = client.get("/v1/definition-validations/" + receipt.json()["outcome"]["committed"]["object_id"], headers=headers).json()
        assert result["structurally_valid"], result["findings"]
        admit = {"encoding": NUMERIC_ENCODING, "identity": {**saved_request["identity"], "command_family": "graph.admit_draft", "command_id": "admit"},
            "payload": {"plan_sha256": result["plan_sha256"], "budget": {"limit": 1},
                "inputs": [{"port": "supplied", "value": {"kind": "number", "value": "0.125", "unit": "1"}}],
                "draft": {key: result[key] for key in ("draft_id", "revision", "content_sha256", "validation_id", "universe_sha256")}}}
        accepted = client.post("/v1/graph-runs/drafts", json=admit, headers=headers)
        assert accepted.status_code == 200, accepted.json()
        assert accepted.json()["outcome"]["status"] == "accepted", accepted.json()
        assert client.post("/v1/graph-runs/drafts", json=admit, headers=headers).json() == accepted.json()
        assert client.post("/v1/definition-drafts/save", json=saved_request, headers=headers).json() == saved
    run = accepted.json()["outcome"]["committed"]["object_id"]
    advance = parse_graph_command("graph.advance", json.dumps({"identity": {**saved_request["identity"], "command_family": "graph.advance", "command_id": "advance"}, "payload": {"run_id": run}}))
    GraphAdvancer(e.engine).advance(e.principal, advance)
    assert GraphReads(e.engine).run(e.principal, run, version=3).status == "completed"
    with e.engine.connect() as connection:
        profiles = connection.execute(text("SELECT family,profile FROM runtime.commands WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).all()
    assert ("definition.save", NUMERIC_ENCODING) in profiles and ("graph.admit_draft", NUMERIC_ENCODING) in profiles
    assert ("definition.validate", "amphora-command-v1") in profiles


def test_numeric_save_survives_actual_host_kill_and_legacy_profile_replay(graph_env, tmp_path, monkeypatch):
    e = graph_env.env
    path, config = graph_host(graph_env, tmp_path, monkeypatch)
    config["authoring"] = True
    config["principals"][0]["actions"].extend(["author", "validate"])
    path.write_text(json.dumps(config), encoding="utf-8")
    env = {**isolated_env(), "TEST_RUNTIME_URL": e.engine.url.render_as_string(hide_password=False), "TEST_RUNTIME_TOKEN": "x" * 32}
    service = Process(sys.executable, "amphora_campaign_runtime", path, env, tmp_path, free_port())
    try:
        service.ready("x" * 32)
        numeric = numeric_save(e)
        saved = decoded(service.endpoint, "/v1/definition-drafts/save", "x" * 32, numeric)
        legacy = json.loads(command(e, "legacy", 1, "Legacy replacement").canonical_bytes)
        old = decoded(service.endpoint, "/v1/definition-drafts/save", "x" * 32, legacy)
        service.kill()
        service.start()
        service.ready("x" * 32)
        assert decoded(service.endpoint, "/v1/definition-drafts/save", "x" * 32, numeric) == saved
        assert decoded(service.endpoint, "/v1/definition-drafts/save", "x" * 32, legacy) == old
        changed_profile = {**legacy, "encoding": NUMERIC_ENCODING}
        assert request(service.endpoint, "/v1/definition-drafts/save", "x" * 32, changed_profile)[0] == 409
        original = decoded(service.endpoint, "/v1/definition-drafts/draft?revision=1", "x" * 32)
        assert original["definition"]["body"]["nodes"][0]["outputs"][0]["source"]["value"] == 1.25
    finally:
        service.close()
