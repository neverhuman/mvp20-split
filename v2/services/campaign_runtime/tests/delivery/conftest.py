"""Runtime-owned delivery evidence with scoped real PostgreSQL state."""

import json
import uuid
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_contracts_runtime import parse_command


@pytest.fixture
def delivery_env(fixture_env):
    e = fixture_env
    principal = replace(e.principal, actions=e.principal.actions | {"deliver", "revoke"})
    def command(family, payload):
        return parse_command(family, json.dumps({"identity": {"command_family": family,
            "command_id": uuid.uuid4().hex, "actor_id": principal.actor_id, "scope": principal.scope.model_dump()},
            "payload": payload}))
    # Policy event before admission proves delivery does not depend on an existing run.
    AuthorityCommands(e.engine).revoke(principal, command("runtime.revoke_worker", {
        "worker_id": "unused-worker", "reason_code": "fixture"}))
    receipt = e.service.admit(principal, command("runtime.admit_fixture", e.raw["payload"]))
    return SimpleNamespace(env=e, principal=principal, run=receipt.outcome.committed.object_id)
