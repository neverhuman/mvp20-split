"""Additive registry command payloads preserve common canonical encoding."""

import copy
import json

import pytest
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_tools import parse_registry_command
from export_schemas import ROOT

FIXTURE = json.loads((ROOT / "contracts/fixtures/v1/tool_releases.json").read_text())[0]


def test_registry_family_and_nested_scope_are_bound_before_canonicalization():
    scope = {"tenant_id": "internal", "project_id": "synthetic"}
    raw = {"identity": {"scope": scope, "actor_id": "admin", "command_id": "register", "command_family": "registry.register"},
           "payload": {"scope": dict(scope), "descriptor": FIXTURE["descriptor"], "expected_lock": FIXTURE["lock"]}}
    command = parse_registry_command("registry.register", json.dumps(raw))
    assert parse_registry_command("registry.register", command.canonical_bytes) == command
    changed = copy.deepcopy(raw)
    changed["payload"]["scope"]["project_id"] = "other"
    with pytest.raises(CommandEncodingError, match="scope_mismatch"):
        parse_registry_command("registry.register", json.dumps(changed))
    changed = copy.deepcopy(raw)
    changed["identity"]["command_family"] = "registry.activate"
    with pytest.raises(CommandEncodingError, match="family_mismatch"):
        parse_registry_command("registry.register", json.dumps(changed))
    with pytest.raises(CommandEncodingError, match="unknown_family"):
        parse_registry_command("registry.unknown", json.dumps(raw))
