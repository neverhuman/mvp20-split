"""Owned graph admission fixtures; actual PostgreSQL, public frozen tool metadata."""

import json
import uuid
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog, ReviewedPlan
from amphora_contracts_graph_runtime import parse_graph_command
from amphora_contracts_runtime import parse_command

from ..compiler.conftest import compiler_env as compiler_env
from ..compiler.conftest import definition


@pytest.fixture
def graph_env(fixture_env, compiler_env):
    env = fixture_env
    env.principal = replace(env.principal, actions=env.principal.actions | {"admit", "maintain", "read", "complete", "cancel"})
    raw = compiler_env.raw[0]
    raw["scope"] = env.principal.scope.model_dump(mode="json")
    reviewed = ReviewedPlan.compile(definition(raw), compiler_env.tools, compiler_env.schemas)
    declaration = raw["body"]["inputs"][0]["value_type"]
    value = {"kind": "artifact", "representation": declaration["representation"], "unit": declaration["unit"], "artifact": {
        "artifact_id": "synthetic-input", "scope": raw["scope"], "sha256": "a" * 64,
        "schema_ref": declaration["schema_ref"], "media_type": "application/json", "size_bytes": 30}}
    payload = {"plan_sha256": reviewed.plan.sha256, "inputs": [{"port": "parameters", "value": value}], "budget": {"limit": 2}}

    def command(family, data, key=None):
        parser = parse_graph_command if family.startswith("graph.") else parse_command
        return parser(family, json.dumps({"identity": {"scope": raw["scope"], "actor_id": env.principal.actor_id,
            "command_family": family, "command_id": key or uuid.uuid4().hex}, "payload": data}))

    return SimpleNamespace(env=env, source=compiler_env, raw=raw, entry=reviewed, payload=payload, command=command,
                           admission=GraphAdmission(env.engine, PlanCatalog([reviewed])))
