"""Actual PostgreSQL admission guards with scripted public Registry observations."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog
from amphora_campaign_runtime.definitions.admission import DraftAdmissionGuard
from amphora_campaign_runtime.definitions.eligibility import RegistryEligibility
from amphora_campaign_runtime.definitions.eligibility.observations import (
    EligibilityUnavailable,
)
from amphora_campaign_runtime.definitions.reads import DefinitionReads
from amphora_campaign_runtime.definitions.validate import DefinitionValidator
from amphora_campaign_runtime.definitions.validation import ValidationUniverse
from amphora_contracts_graph_runtime import parse_authoring_command
from sqlalchemy import text

from .test_admission import graph_command, prepared
from .test_commands import bindings, command
from .test_eligibility import candidate
from .test_validate import request


def eligible(graph_env, monkeypatch, *, mode="candidate"):
    g, e = graph_env, graph_env.env
    saves, _, _ = prepared(e)
    raw = json.loads(command(e, "tool-draft", 1).canonical_bytes)
    raw["payload"]["definition"] = {
        **g.raw,
        "schema_version": "4",
        "profile": "deterministic-v3",
        "campaign_id": "research",
    }
    saves.save(e.principal, parse_authoring_command("definition.save", json.dumps(raw)))
    universe = ValidationUniverse(
        e.principal.scope, (g.source.tool,), tuple(g.source.schema_list)
    )
    universes = {(e.principal.scope.tenant_id, e.principal.scope.project_id): universe}
    receipt = DefinitionValidator(e.engine, universes).validate(
        e.principal, request(e, "tools", revision=2)
    )
    validation = DefinitionReads(e.engine).validation(
        e.principal, receipt.outcome.committed.object_id
    )
    assert validation.structurally_valid
    peer = RegistryEligibility("http://127.0.0.1:1", "s" * 32, "selector")
    calls = []

    def resolve(command, timeout):
        calls.append(command)
        # An independent connection can take admission_guard while peer I/O runs.
        with e.engine.begin() as conn:
            conn.execute(
                text(
                    "SELECT singleton FROM runtime.admission_guard WHERE singleton=true FOR UPDATE NOWAIT"
                )
            )
        if mode == "network":
            raise EligibilityUnavailable("draft_registry_unavailable")
        at = (
            datetime.now(UTC) - timedelta(seconds=10)
            if mode == "expired"
            else datetime.now(UTC)
        )
        observed = candidate(g.source.tool, e.principal.scope, at)
        if mode == "rejected":
            observed = observed.model_copy(
                update={"status": "rejected", "reason_code": "no_eligible_capacity"}
            )
        return observed

    monkeypatch.setattr(peer, "_resolve", resolve)
    guard = DraftAdmissionGuard(e.engine, universes, peer)
    service = GraphAdmission(
        e.engine, PlanCatalog([]), bindings_enabled=True, drafts=guard
    )
    payload = {
        "plan_sha256": validation.plan_sha256,
        "inputs": g.payload["inputs"],
        "budget": {"limit": 2},
        "draft": {
            "draft_id": validation.draft_id,
            "revision": validation.revision,
            "content_sha256": validation.content_sha256,
            "validation_id": validation.validation_id,
            "universe_sha256": validation.universe_sha256,
        },
    }
    return service, payload, calls, saves


def test_tool_admission_records_observation_and_terminal_replay_does_not_refresh_it(
    graph_env, monkeypatch
):
    e = graph_env.env
    service, payload, calls, _ = eligible(graph_env, monkeypatch)
    command = graph_command(e, "graph.admit_draft", "eligible", payload)
    receipt = service.admit_draft(e.principal, command)
    assert receipt.outcome.status == "accepted"
    assert len(calls) == 1
    with e.engine.connect() as conn:
        record = conn.execute(
            text(
                "SELECT payload FROM runtime.audit_events WHERE tenant_id=:tenant AND project_id=:project "
                "AND payload->>'kind'='draft_eligibility_observed'"
            ),
            bindings(e),
        ).scalar_one()
        assert record["reservation"] is False
        assert record["observations"][0]["request_sha256"] == calls[0].sha256
        assert (
            record["observations"][0]["receipt"]["operation_id"]
            == "registry-observation"
        )
    service.drafts = None
    assert service.admit_draft(e.principal, command) == receipt
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("mode", "reason"),
    [
        ("expired", "draft_tool_eligibility_expired"),
        ("network", "draft_registry_unavailable"),
        ("rejected", "draft_tool_ineligible"),
    ],
)
def test_unusable_observation_rejects_atomically_and_replay_remains_original(
    graph_env, monkeypatch, mode, reason
):
    e = graph_env.env
    service, payload, calls, _ = eligible(graph_env, monkeypatch, mode=mode)
    command = graph_command(e, "graph.admit_draft", "unavailable", payload)
    receipt = service.admit_draft(e.principal, command)
    assert (
        receipt.outcome.status == "rejected" and receipt.outcome.reason_code == reason
    )
    assert service.admit_draft(e.principal, command) == receipt and len(calls) == 1
    with e.engine.connect() as conn:
        for table in ["runs", "definition_admissions"]:
            assert (
                conn.execute(
                    text(
                        f"SELECT count(*) FROM runtime.{table} WHERE tenant_id=:tenant AND project_id=:project"
                    ),
                    bindings(e),
                ).scalar_one()
                == 0
            )


def test_newer_head_and_active_campaign_still_reject_with_eligible_tools(
    graph_env, monkeypatch
):
    e = graph_env.env
    service, payload, _, saves = eligible(graph_env, monkeypatch)
    accepted = service.admit_draft(
        e.principal, graph_command(e, "graph.admit_draft", "first", payload)
    )
    assert accepted.outcome.status == "accepted"
    blocked = service.admit_draft(
        e.principal, graph_command(e, "graph.admit_draft", "second", payload)
    )
    assert blocked.outcome.reason_code == "active_run_exists"
    saves.save(e.principal, command(e, "newer-head", 2))
    stale = service.admit_draft(
        e.principal, graph_command(e, "graph.admit_draft", "stale", payload)
    )
    assert stale.outcome.reason_code == "draft_head_changed"


def test_failed_observation_audit_rolls_back_publication_and_run(
    graph_env, monkeypatch
):
    e = graph_env.env
    service, payload, _, _ = eligible(graph_env, monkeypatch)
    original = service.drafts.record

    def interrupted(*args):
        original(*args)
        raise RuntimeError("before_commit")

    monkeypatch.setattr(service.drafts, "record", interrupted)
    command = graph_command(e, "graph.admit_draft", "interrupt", payload)
    with pytest.raises(RuntimeError, match="before_commit"):
        service.admit_draft(e.principal, command)
    with e.engine.connect() as conn:
        for table in ["runs", "definition_admissions", "audit_events"]:
            assert (
                conn.execute(
                    text(
                        f"SELECT count(*) FROM runtime.{table} WHERE tenant_id=:tenant AND project_id=:project"
                    ),
                    bindings(e),
                ).scalar_one()
                == 0
            )
    monkeypatch.setattr(service.drafts, "record", original)
    assert service.admit_draft(e.principal, command).outcome.status == "accepted"
