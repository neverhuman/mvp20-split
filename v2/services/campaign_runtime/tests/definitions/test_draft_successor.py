"""Real owner transactions combine draft guards with terminal predecessor carry."""

import copy
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.definitions.admission import DraftAdmissionGuard
from amphora_campaign_runtime.definitions.reads import DefinitionReads
from amphora_campaign_runtime.successors.reads import SuccessorReads
from amphora_contracts_draft_successor import parse_draft_successor
from amphora_contracts_graph_runtime import parse_authoring_command
from sqlalchemy import text

from .test_admission import graph_command
from .test_commands import bindings, command
from .test_validate import request, setup


def prepare(e, *, finish=True):
    saves, validator, universe = setup(e)
    e.principal = replace(e.principal, actions=e.principal.actions | {"admit", "maintain"})
    raw = json.loads(command(e, "scalar", 1).canonical_bytes)
    scalar = {"kind": "scalar", "scalar": "integer", "unit": "1"}
    raw["payload"]["definition"]["body"] = {
        "inputs": [{"name": "value", "value_type": scalar}], "outputs": [{"name": "value", "value_type": scalar}],
        "nodes": [{"kind": "finish", "node_id": "done", "outputs": [{"port": "value", "source": {"kind": "input", "name": "value"}}]}],
        "edges": []}
    saves.save(e.principal, parse_authoring_command("definition.save", json.dumps(raw)))
    guard = DraftAdmissionGuard(e.engine, {(e.principal.scope.tenant_id, e.principal.scope.project_id): universe})
    service = GraphAdmission(e.engine, PlanCatalog([]), bindings_enabled=True, drafts=guard)

    def validated(revision):
        receipt = validator.validate(e.principal, request(e, f"validate-{revision}", revision=revision))
        validation = DefinitionReads(e.engine).validation(e.principal, receipt.outcome.committed.object_id)
        assert validation.structurally_valid
        return {"plan_sha256": validation.plan_sha256, "inputs": [], "budget": {"limit": 1},
                "draft": {key: getattr(validation, key) for key in
                          ("draft_id", "revision", "content_sha256", "validation_id", "universe_sha256")}}

    parent = validated(2)
    parent["inputs"] = [{"port": "value", "value": {"kind": "integer", "value": 17}}]
    receipt = service.admit_draft(e.principal, graph_command(e, "graph.admit_draft", "parent", parent))
    assert receipt.outcome.status == "accepted"
    run = receipt.outcome.committed.object_id
    if finish:
        GraphAdvancer(e.engine).advance(e.principal, graph_command(e, "graph.advance", "finish", {"run_id": run}))
    raw["identity"]["command_id"] = "successor-draft"
    raw["payload"]["expected_revision"] = 2
    raw["payload"]["definition"]["revision"] = 2
    saves.save(e.principal, parse_authoring_command("definition.save", json.dumps(raw)))
    payload = validated(3)
    from amphora_campaign_runtime.coordinator.reads import GraphReads
    view = GraphReads(e.engine).run(e.principal, run, version=3)
    payload.update(predecessor={"run_id": run, "plan_sha256": parent["plan_sha256"], "revision": view.revision}, carried=[])
    if finish:
        observed = SuccessorReads(e.engine).sources(e.principal, run)
        source = observed.sources[0]
        payload["carried"] = [{"target_port": "value", "source": source.source.model_dump(mode="json"),
                               "expected_value_sha256": source.value_sha256}]
    return saves, service, payload, run


def next_command(e, payload, key="successor"):
    return parse_draft_successor(json.dumps({"identity": {"scope": e.principal.scope.model_dump(),
        "actor_id": e.principal.actor_id, "command_family": "graph.admit_draft_successor", "command_id": key}, "payload": payload}))


def test_combined_admission_carries_value_and_preserves_replay_after_configuration_removal(fixture_env):
    e = fixture_env
    saves, service, payload, parent = prepare(e)
    cmd = next_command(e, payload)
    receipt = service.admit_draft_successor(e.principal, cmd)
    assert receipt.outcome.status == "accepted"
    run = receipt.outcome.committed.object_id
    lineage = SuccessorReads(e.engine).lineage(e.principal, run)
    assert lineage.predecessor.run_id == parent and lineage.carried[0].expected_value_sha256 == payload["carried"][0]["expected_value_sha256"]
    with e.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.definition_admissions WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one() == 2
    saves.save(e.principal, command(e, "later-head", 3, "Future only"))
    replacement = GraphAdmission(e.engine, PlanCatalog([]), drafts=None)
    assert replacement.admit_draft_successor(e.principal, cmd) == receipt
    GraphAdvancer(e.engine).advance(e.principal, graph_command(e, "graph.advance", "finish-child", {"run_id": run}))
    assert SuccessorReads(e.engine).sources(e.principal, run).sources[0].value_sha256 == payload["carried"][0]["expected_value_sha256"]
    assert SuccessorReads(e.engine).lineage(e.principal, run) == lineage


@pytest.mark.parametrize("case,reason", [
    ("cut", "predecessor_cut_changed"), ("hash", "carry_value_changed"),
    ("head", "draft_head_changed"), ("universe", "draft_universe_changed"),
    ("selection", "draft_validation_selection_mismatch"), ("disabled", "draft_admission_not_enabled"),
    ("foreign", "predecessor_unavailable"), ("overlap", "duplicate_graph_input"),
    ("target", "graph_input_ports_mismatch"),
])
def test_both_guard_families_reject_durably_without_lineage(fixture_env, case, reason):
    e = fixture_env
    saves, service, payload, _ = prepare(e)
    if case == "cut": payload["predecessor"]["revision"] += 1
    elif case == "hash": payload["carried"][0]["expected_value_sha256"] = "f" * 64
    elif case == "head": saves.save(e.principal, command(e, "later", 3, "Later"))
    elif case == "universe": service.drafts = DraftAdmissionGuard(e.engine, {})
    elif case == "selection": payload["draft"]["content_sha256"] = "f" * 64
    elif case == "disabled": service.drafts = None
    elif case == "foreign": payload["predecessor"]["run_id"] = "foreign"
    elif case == "overlap": payload["inputs"] = [{"port": "value", "value": {"kind": "integer", "value": 1}}]
    elif case == "target": payload["carried"][0]["target_port"] = "absent"
    cmd = next_command(e, payload)
    receipt = service.admit_draft_successor(e.principal, cmd)
    assert receipt.outcome.reason_code == reason
    assert service.admit_draft_successor(e.principal, cmd) == receipt
    with e.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.graph_successors WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one() == 0


def test_active_predecessor_cannot_be_adopted(fixture_env):
    e = fixture_env
    _, service, payload, _ = prepare(e, finish=False)
    receipt = service.admit_draft_successor(e.principal, next_command(e, payload))
    assert receipt.outcome.status == "rejected"
    assert receipt.outcome.reason_code == "predecessor_not_terminal"


def test_publication_failure_rolls_back_successor_lineage_and_retry_recovers(fixture_env, monkeypatch):
    e = fixture_env
    _, service, payload, _ = prepare(e)
    original = service.drafts.record
    def fail(*args):
        original(*args)
        raise RuntimeError("after_both_records")
    monkeypatch.setattr(service.drafts, "record", fail)
    cmd = next_command(e, payload)
    with pytest.raises(RuntimeError, match="after_both_records"):
        service.admit_draft_successor(e.principal, cmd)
    with e.engine.connect() as conn:
        for table, count in (("runs", 1), ("definition_admissions", 1), ("graph_successors", 0)):
            assert conn.execute(text(f"SELECT count(*) FROM runtime.{table} WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one() == count
    monkeypatch.setattr(service.drafts, "record", original)
    assert service.admit_draft_successor(e.principal, cmd).outcome.status == "accepted"


def test_concurrent_successors_share_single_active_guard(fixture_env):
    e = fixture_env
    _, service, payload, _ = prepare(e)
    barrier = Barrier(2)
    def admit(key):
        barrier.wait(timeout=5)
        return service.admit_draft_successor(e.principal, next_command(e, copy.deepcopy(payload), key))
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(admit, ("one", "two")))
    assert sorted(r.outcome.status for r in receipts) == ["accepted", "rejected"]
    assert next(r for r in receipts if r.outcome.status == "rejected").outcome.reason_code == "active_run_exists"


def test_authenticated_route_and_explicit_configuration(fixture_env):
    from amphora_campaign_runtime.api import create_app
    from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
    from fastapi.testclient import TestClient
    e = fixture_env
    _, service, payload, _ = prepare(e)
    credentials = RuntimeCredentials([("s" * 32, e.principal),
        ("r" * 32, replace(e.principal, actions=frozenset({"read"})))])
    route = "/v1/graph-runs/draft-successors"
    raw = next_command(e, payload).canonical_bytes
    with TestClient(create_app(e.service, credentials, graphs=(service, GraphAdvancer(e.engine)))) as client:
        assert client.post(route, content=raw).status_code == 401
        assert client.post(route, content=raw, headers={"Authorization": "Bearer " + "r" * 32}).status_code == 403
        headers = {"Authorization": "Bearer " + "s" * 32}
        accepted = client.post(route, content=raw, headers=headers)
        assert accepted.status_code == 200 and accepted.json()["outcome"]["status"] == "accepted"
        assert client.post(route, content=raw, headers=headers).json() == accepted.json()
        assert client.post(route, content=b"{}", headers=headers).status_code == 422
    disabled = GraphAdmission(e.engine, PlanCatalog([]))
    with TestClient(create_app(e.service, credentials, graphs=(disabled, GraphAdvancer(e.engine)))) as client:
        assert client.post(route, content=raw, headers=headers).status_code == 405
        assert route not in client.get("/openapi.json").json()["paths"]


def test_head_change_between_preparation_and_transaction_is_rechecked(fixture_env, monkeypatch):
    e = fixture_env
    saves, service, payload, _ = prepare(e)
    original = service.drafts.prepare
    def change_head(*args):
        material = original(*args)
        saves.save(e.principal, command(e, "raced-head", 3, "Future"))
        return material
    monkeypatch.setattr(service.drafts, "prepare", change_head)
    assert service.admit_draft_successor(e.principal, next_command(e, payload)).outcome.reason_code == "draft_head_changed"


@pytest.mark.parametrize("mode,reason", [("candidate", None), ("expired", "draft_tool_eligibility_expired"),
                                        ("network", "draft_registry_unavailable"), ("rejected", "draft_tool_ineligible")])
def test_combined_command_preserves_current_registry_guard_and_original_replay(graph_env, monkeypatch, mode, reason):
    from datetime import UTC, datetime, timedelta
    from amphora_campaign_runtime.definitions.eligibility import RegistryEligibility
    from amphora_campaign_runtime.definitions.eligibility.observations import EligibilityUnavailable
    from amphora_campaign_runtime.definitions.validate import DefinitionValidator
    from amphora_campaign_runtime.definitions.validation import ValidationUniverse
    from .test_eligibility import candidate
    g, e = graph_env, graph_env.env
    saves, _, original, _ = prepare(e)
    raw = json.loads(command(e, "tool-successor", 3).canonical_bytes)
    raw["payload"]["definition"] = {**g.raw, "schema_version": "4", "profile": "deterministic-v3", "campaign_id": "research"}
    saves.save(e.principal, parse_authoring_command("definition.save", json.dumps(raw)))
    universe = ValidationUniverse(e.principal.scope, (g.source.tool,), tuple(g.source.schema_list))
    universes = {(e.principal.scope.tenant_id, e.principal.scope.project_id): universe}
    receipt = DefinitionValidator(e.engine, universes).validate(e.principal, request(e, "tools", revision=4))
    validation = DefinitionReads(e.engine).validation(e.principal, receipt.outcome.committed.object_id)
    assert validation.structurally_valid
    peer = RegistryEligibility("http://127.0.0.1:1", "s" * 32, "selector")
    calls = []
    def resolve(command, timeout):
        calls.append(command)
        with e.engine.begin() as conn:
            conn.execute(text("SELECT singleton FROM runtime.admission_guard WHERE singleton=true FOR UPDATE NOWAIT"))
        if mode == "network": raise EligibilityUnavailable("draft_registry_unavailable")
        at = datetime.now(UTC) - timedelta(seconds=10) if mode == "expired" else datetime.now(UTC)
        result = candidate(g.source.tool, e.principal.scope, at)
        return result.model_copy(update={"status": "rejected", "reason_code": "no_eligible_capacity"}) if mode == "rejected" else result
    monkeypatch.setattr(peer, "_resolve", resolve)
    service = GraphAdmission(e.engine, PlanCatalog([]), bindings_enabled=True, drafts=DraftAdmissionGuard(e.engine, universes, peer))
    payload = {"plan_sha256": validation.plan_sha256, "inputs": g.payload["inputs"], "budget": {"limit": 2},
               "draft": {key: getattr(validation, key) for key in ("draft_id", "revision", "content_sha256", "validation_id", "universe_sha256")},
               "predecessor": original["predecessor"], "carried": []}
    cmd = next_command(e, payload)
    receipt = service.admit_draft_successor(e.principal, cmd)
    if reason is None:
        assert receipt.outcome.status == "accepted"
        assert SuccessorReads(e.engine).lineage(e.principal, receipt.outcome.committed.object_id).predecessor.run_id == original["predecessor"]["run_id"]
    else:
        assert receipt.outcome.reason_code == reason
    assert len(calls) == 1
    service.drafts = None
    assert service.admit_draft_successor(e.principal, cmd) == receipt
    assert len(calls) == 1
