"""Runtime-owned synthetic completion fixtures; no scientific artifact validity."""

import copy
import json
import uuid
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.lifecycle.admission import FixtureAdmission, FixtureCatalog
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_contracts_runtime import AdmitFixtureRun, parse_command
from amphora_contracts_tools import ToolDescriptor


@pytest.fixture
def completion_env(fixture_env, request):
    e = fixture_env
    e.principal = replace(e.principal, actions=e.principal.actions | {"complete", "cancel", "revoke", "read"})
    e.raw["payload"]["invocations"][0]["timeout_seconds"] = 120
    spec = e.raw["payload"]["invocations"][0]
    if getattr(request, "param", 1) == 2:
        second = copy.deepcopy(spec)
        second.update(activation_id="iteration-1.n2", invocation_id="i2", node_id="n2")
        e.raw["payload"]["invocations"].append(second)
    schema = spec["inputs"][0]["artifact"]["schema_ref"]
    port = {"name": "value", "schema_ref": schema, "representation": "synthetic", "unit": "1"}
    descriptor = ToolDescriptor.model_validate_json(json.dumps({"schema_version": "1", "binding": spec["tool"],
        "purpose": "Synthetic lifecycle acceptance only", "applicability": ["test"],
        "inputs": [port], "outputs": [port], "side_effects": "pure", "checkpoint_schema": schema}))
    e.service = FixtureAdmission(e.engine, FixtureCatalog(
        [AdmitFixtureRun.model_validate_json(json.dumps(e.raw["payload"]))], [descriptor]))

    def command(family, payload, identity=None):
        return parse_command(family, json.dumps({"identity": {"command_family": family,
            "command_id": identity or uuid.uuid4().hex, "actor_id": e.principal.actor_id,
            "scope": e.principal.scope.model_dump()}, "payload": payload}))
    run = e.service.admit(e.principal, command("runtime.admit_fixture", e.raw["payload"])).outcome.committed.object_id
    invocation = RuntimeLeases(e.engine).claim(e.principal, command("runtime.claim", {
        "run_id": run, "worker_id": e.principal.actor_id, "tool": spec["tool"], "lease_seconds": 90})).outcome.invocation
    artifact = {**spec["inputs"][0]["artifact"], "artifact_id": "synthetic-output"}
    payload = {"run_id": run, "completion": {"schema_version": "1", "invocation_id": invocation.invocation_id,
        "attempt_id": invocation.attempt_id, "fence": invocation.fence,
        "outcome": {"status": "succeeded", "outputs": [{"port": "value", "artifact": artifact}]}}}
    return SimpleNamespace(env=e, run=run, invocation=invocation, command=command, payload=payload, descriptor=descriptor)
