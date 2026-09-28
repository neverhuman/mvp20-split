"""JSON-only independent wheel probe; never imports peer implementations."""

import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import amphora_capability_registry
from amphora_capability_registry.descriptors.assessments import CapacityObservation
from amphora_capability_registry.descriptors.identity import ReleaseDocument
from amphora_capability_registry.descriptors.policy import (
    EligibilityEvaluator,
    EvaluationPolicy,
    PermissionPolicy,
)
from amphora_capability_registry.descriptors.requirements import CapabilityNeed, ResourceAllowance
from amphora_contracts_core import Scope
from amphora_contracts_tools import LockEntry, ReleaseDescriptor

assert Path(amphora_capability_registry.__file__).is_relative_to(sys.prefix), "Must use installed wheel"
assert Path(amphora_capability_registry.__file__).parent.joinpath("persistence/migrations/versions/r0001_initial.sql").is_file()
for absent in ("amphora_campaign_runtime", "amphora_data_artifacts", "torch", "rdkit"):
    assert importlib.util.find_spec(absent) is None, absent

request = json.loads(sys.stdin.readline())
release = ReleaseDescriptor.model_validate_json(json.dumps(request["descriptor"]))
document = ReleaseDocument.from_descriptor(release)
if "lock" in request:
    document.verify_lock(LockEntry.model_validate_json(json.dumps(request["lock"])))
    assert document.canonical_bytes.decode() == request["canonical_utf8"]
scope = Scope(tenant_id="installed", project_id="descriptor-proof")
need = CapabilityNeed.for_tool(scope, request.get("context", "synthetic-tests"), release.tool)
now = datetime(2026, 9, 28, 12, tzinfo=UTC)
capacity = CapacityObservation(scope, document.digest, 1, 1, now, now + timedelta(seconds=30))
policy = EvaluationPolicy(scope, ResourceAllowance("x86_64", "windows", 4000, 4096, 0, 300, 8, 128), PermissionPolicy())
decision = EligibilityEvaluator().evaluate(release, need, policy, capacity, now=now).to_wire()
assert decision.status == request.get("expected_status", "candidate")
print(json.dumps({"canonical_utf8": document.canonical_bytes.decode(), "lock": document.to_lock().model_dump(mode="json"),
                  "descriptor": release.model_dump(mode="json"), "tool": release.tool.model_dump(mode="json"),
                  "decision": decision.model_dump(mode="json")}, sort_keys=True))
