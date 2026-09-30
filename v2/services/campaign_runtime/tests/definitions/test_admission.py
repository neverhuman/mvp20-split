"""Draft admission uses the existing run transaction; publication is not future admission authority."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_campaign_runtime.definitions.admission import DraftAdmissionGuard
from amphora_campaign_runtime.definitions.published import PublishedPlanCatalog
from amphora_campaign_runtime.definitions.reads import DefinitionReads
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import parse_graph_command
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .test_commands import bindings, command
from .test_validate import request, setup


def graph_command(e, family, key, payload):
    return parse_graph_command(family, json.dumps({"identity": {"scope": e.principal.scope.model_dump(),
        "actor_id": e.principal.actor_id, "command_family": family, "command_id": key}, "payload": payload}))


def prepared(e):
    saves, validator, universe = setup(e)
    e.principal = replace(e.principal, actions=e.principal.actions | {"admit", "maintain"})
    receipt = validator.validate(e.principal, request(e))
    validation = DefinitionReads(e.engine).validation(e.principal, receipt.outcome.committed.object_id)
    guard = DraftAdmissionGuard(e.engine, {(e.principal.scope.tenant_id, e.principal.scope.project_id): universe})
    service = GraphAdmission(e.engine, PlanCatalog([]), bindings_enabled=True, drafts=guard)
    payload = {"plan_sha256": validation.plan_sha256, "inputs": [], "budget": {"limit": 1}, "draft": {
        "draft_id": validation.draft_id, "revision": validation.revision, "content_sha256": validation.content_sha256,
        "validation_id": validation.validation_id, "universe_sha256": validation.universe_sha256}}
    return saves, service, payload


def test_admitted_plan_restores_but_cannot_bypass_draft_admission(fixture_env):
    e = fixture_env
    saves, service, payload = prepared(e)
    request = graph_command(e, "graph.admit_draft", "admit", payload)
    receipt = service.admit_draft(e.principal, request)
    assert receipt.outcome.status == "accepted"
    run = receipt.outcome.committed.object_id
    restored = PublishedPlanCatalog(e.engine, PlanCatalog([])).require(e.principal.scope, payload["plan_sha256"])
    assert restored.plan.sha256 == payload["plan_sha256"]
    general = {key: value for key, value in payload.items() if key != "draft"}
    assert service.admit(e.principal, graph_command(e, "graph.admit", "bypass", general)).outcome.reason_code == "graph_plan_unavailable"
    saves.save(e.principal, command(e, "edit-while-running", 1, "Next campaign"))
    replacement = GraphAdmission(e.engine, PlanCatalog([]), drafts=None)
    assert replacement.admit_draft(e.principal, request) == receipt
    GraphAdvancer(e.engine).advance(e.principal, graph_command(e, "graph.advance", "advance", {"run_id": run}))
    assert GraphReads(e.engine).run(e.principal, run, version=3).status == "completed"
    assert PublishedPlanCatalog(e.engine, PlanCatalog([])).require(e.principal.scope, payload["plan_sha256"]).plan == restored.plan
    with pytest.raises(TransitionError, match="graph_plan_unavailable"):
        PublishedPlanCatalog(e.engine, PlanCatalog([])).require(Scope(tenant_id="foreign", project_id="foreign"), payload["plan_sha256"])
    with pytest.raises(DBAPIError), e.engine.begin() as conn:
        conn.execute(text("DELETE FROM runtime.definition_admissions WHERE tenant_id=:tenant AND project_id=:project"), bindings(e))
    with pytest.raises(TransitionError, match="access_denied"):
        replacement.admit_draft(replace(e.principal, actions=frozenset({"read"})), request)


def test_head_or_universe_change_rejects_without_publication(fixture_env):
    e = fixture_env
    saves, service, payload = prepared(e)
    unavailable = GraphAdmission(e.engine, PlanCatalog([]), bindings_enabled=True,
        drafts=DraftAdmissionGuard(e.engine, {}))
    rejected = unavailable.admit_draft(e.principal, graph_command(e, "graph.admit_draft", "changed-universe", payload))
    assert rejected.outcome.reason_code == "draft_universe_changed"
    saves.save(e.principal, command(e, "edit", 1, "New head"))
    stale = service.admit_draft(e.principal, graph_command(e, "graph.admit_draft", "stale", payload))
    assert stale.outcome.reason_code == "draft_head_changed"
    with pytest.raises(TransitionError, match="graph_plan_unavailable"):
        PublishedPlanCatalog(e.engine, PlanCatalog([])).require(e.principal.scope, payload["plan_sha256"])


def test_publication_failure_rolls_back_run_and_original_receipt(fixture_env, monkeypatch):
    e = fixture_env
    _, service, payload = prepared(e)
    original = service.drafts.record

    def fail(*args):
        original(*args)
        raise RuntimeError("publication_before_receipt")

    monkeypatch.setattr(service.drafts, "record", fail)
    request = graph_command(e, "graph.admit_draft", "admit", payload)
    with pytest.raises(RuntimeError, match="publication_before_receipt"):
        service.admit_draft(e.principal, request)
    with e.engine.connect() as conn:
        for table in ("runs", "graph_plans", "definition_admissions"):
            assert conn.execute(text(f"SELECT count(*) FROM runtime.{table} WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one() == 0
        assert conn.execute(text("SELECT status FROM runtime.commands WHERE tenant_id=:tenant AND project_id=:project "
            "AND family='graph.admit_draft' AND command_id='admit'"), bindings(e)).scalar_one() == "pending"
    monkeypatch.setattr(service.drafts, "record", original)
    assert service.admit_draft(e.principal, request).outcome.status == "accepted"


def test_two_draft_admissions_share_the_single_campaign_guard(fixture_env):
    e = fixture_env
    _, service, payload = prepared(e)
    barrier = Barrier(2)

    def run(key):
        barrier.wait(timeout=5)
        return service.admit_draft(e.principal, graph_command(e, "graph.admit_draft", key, payload))

    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(run, ("first", "second")))
    assert sorted(r.outcome.status for r in receipts) == ["accepted", "rejected"]
    assert next(r for r in receipts if r.outcome.status == "rejected").outcome.reason_code == "active_run_exists"


def test_tool_draft_waits_for_current_eligibility_adapter(fixture_env, compiler_env):
    from copy import deepcopy

    from amphora_campaign_runtime.definitions.validate import DefinitionValidator
    from amphora_campaign_runtime.definitions.validation import ValidationUniverse
    from amphora_contracts_graph_runtime import parse_authoring_command
    e = fixture_env
    saves, _, _ = prepared(e)
    raw = json.loads(command(e, "tool-draft", 1).canonical_bytes)
    definition = deepcopy(compiler_env.raw[0])
    definition.update(schema_version="4", profile="deterministic-v3", campaign_id="research", scope=e.principal.scope.model_dump())
    raw["payload"]["definition"] = definition
    saves.save(e.principal, parse_authoring_command("definition.save", json.dumps(raw)))
    universe = ValidationUniverse(e.principal.scope, (compiler_env.tool,), tuple(compiler_env.schema_list))
    universes = {(e.principal.scope.tenant_id, e.principal.scope.project_id): universe}
    validation_receipt = DefinitionValidator(e.engine, universes).validate(e.principal, request(e, "tools", revision=2))
    validation = DefinitionReads(e.engine).validation(e.principal, validation_receipt.outcome.committed.object_id)
    assert validation.structurally_valid
    payload = {"plan_sha256": validation.plan_sha256, "inputs": [], "budget": {"limit": 2}, "draft": {
        "draft_id": validation.draft_id, "revision": validation.revision, "content_sha256": validation.content_sha256,
        "validation_id": validation.validation_id, "universe_sha256": validation.universe_sha256}}
    service = GraphAdmission(e.engine, PlanCatalog([]), bindings_enabled=True, drafts=DraftAdmissionGuard(e.engine, universes))
    receipt = service.admit_draft(e.principal, graph_command(e, "graph.admit_draft", "tool-admit", payload))
    assert receipt.outcome.reason_code == "draft_tool_eligibility_unavailable"
