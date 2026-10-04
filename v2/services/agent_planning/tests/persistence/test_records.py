import json
from pathlib import Path

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.persistence.records import verified_observation
from amphora_agent_planning.providers import FixtureProvider, observe
from amphora_agent_planning.providers.capture import Observation
from amphora_contracts_core import Scope
from amphora_contracts_planning import reference_proposal_schema


def test_principal_copies_grants_and_rejects_unrecognized_authority():
    scope = Scope(tenant_id="t", project_id="p")
    grants = {"read_attempts"}
    principal = Principal("actor", scope, grants)
    grants.add("record_requests")
    assert principal.actions == frozenset({"read_attempts"})
    with pytest.raises(ValueError, match="unknown_planning_grant"):
        Principal("actor", scope, frozenset({"execute_code"}))
    with pytest.raises(PermissionError):
        principal.require("read_attempts", Scope(tenant_id="t", project_id="other"))


@pytest.mark.parametrize("field,value,code", [
    ("captured_bytes", 0, "capture_size_mismatch"),
    ("output_complete", False, "capture_completion_mismatch"),
    ("proposal", None, "proposal_status_mismatch"),
    ("status", "proposed", "proposal_status_mismatch"),
    ("reason_code", "invented", "successful_reason"),
])
def test_observation_metadata_cannot_reinterpret_preserved_bytes(field, value, code):
    raw = json.loads((Path(__file__).parents[1] / "context/fixtures/request.json").read_bytes())
    raw["context"]["output_schema"] = reference_proposal_schema().model_dump(mode="json")
    scope = Scope.model_validate(raw["reference"]["scope"])
    snapshot = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id="fixture", scope=scope)
    binding = AttemptBinding(snapshot, 1)
    original = observe(binding, FixtureProvider("abstain"))
    wire = original.document().model_copy(update={field: value})
    forged = Observation(original.capture, wire.model_dump_json().encode())
    with pytest.raises(ValueError, match=code):
        verified_observation(binding, forged)
