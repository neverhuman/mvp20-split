"""Storage-only v3 scaffold; public graph admission remains explicitly gated."""

import json
import uuid
from datetime import timedelta
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.compiler import ToolCatalog
from amphora_campaign_runtime.coordinator import FrontierPlanner, ReviewedPlan, ScopeAddress
from amphora_campaign_runtime.coordinator.storage import GraphStorage
from amphora_campaign_runtime.coordinator.values import BoundValues
from amphora_campaign_runtime.waits import ReceiptEvidence, WaitAddress, WaitRecord
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import ArtifactRef
from amphora_contracts_graph_runtime import DomainReceipt, GraphBinding
from export_schemas import ROOT
from sqlalchemy import text

from ..compiler.conftest import compiler_env as compiler_env
from ..scheduling.conftest import graph_env as graph_env


@pytest.fixture
def wait_env(fixture_env, compiler_env, request):
    env = fixture_env
    raw = json.loads((ROOT / "contracts/fixtures/v3/await_cases.json").read_bytes())[0]["payload"]
    raw["scope"] = env.principal.scope.model_dump(mode="json")
    raw["body"]["nodes"][0]["timeout_seconds"] = getattr(request, "param", 60)
    definition = parse_executable_campaign(json.dumps(raw))
    entry = ReviewedPlan.compile(definition, ToolCatalog([]), compiler_env.schemas)
    subject = ArtifactRef.model_validate_json(json.dumps({"artifact_id": "subject", "scope": raw["scope"],
        "sha256": "a" * 64, "schema_ref": raw["body"]["inputs"][0]["value_type"]["schema_ref"],
        "media_type": "application/json", "size_bytes": 2}))
    value_type = raw["body"]["inputs"][0]["value_type"]
    inputs = BoundValues((GraphBinding.model_validate_json(json.dumps({"port": "parameters", "value": {
        "kind": "artifact", "artifact": subject.model_dump(mode="json"),
        "representation": value_type["representation"], "unit": value_type["unit"]}})),))
    params = {"tenant": env.principal.scope.tenant_id, "project": env.principal.scope.project_id, "run": uuid.uuid4().hex}
    address = ScopeAddress(entry.plan.sha256)
    intents = FrontierPlanner().scope(entry.plan, address)
    with env.engine.begin() as conn:
        now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
        deadline = now + timedelta(seconds=300)
        GraphStorage.retain_plan(conn, params, entry)
        conn.execute(text("INSERT INTO runtime.runs (tenant_id,project_id,run_id,fixture_id,plan_sha256,input_snapshot,"
            "status,budget_limit,execution_mode) VALUES (:tenant,:project,:run,'wait-storage-fixture',:sha,"
            "'{}','running',2,'graph')"), {**params, "sha": entry.plan.sha256})
        conn.execute(text("INSERT INTO runtime.graph_runs (tenant_id,project_id,run_id,plan_sha256,inputs,max_activations,deadline) "
            "VALUES (:tenant,:project,:run,:sha,CAST(:inputs AS jsonb),100,:deadline)"),
            {**params, "sha": entry.plan.sha256, "inputs": json.dumps(inputs.record()), "deadline": deadline})
        GraphStorage.create_scope(conn, params, address, inputs, intents)
    activation = next(item.address.key for item in intents if item.kind == "await")
    record = WaitRecord.pin(WaitAddress(env.principal.scope, params["run"], activation, entry.plan.sha256),
                           definition.body.nodes[0], subject, opened_at=now, run_deadline=deadline)
    expected = record.expectation
    receipt = ReceiptEvidence(DomainReceipt.model_validate_json(json.dumps({
        "issuer_id": expected.issuer_id, "receipt_id": "evidence-1", "scope": raw["scope"], "purpose": expected.purpose,
        "revision": expected.expected_revision, "subject": subject.model_dump(mode="json"), "outcome": {
            "status": "accepted", "output": {"kind": "artifact", "representation": expected.output_type.representation,
            "unit": expected.output_type.unit, "artifact": {**subject.model_dump(mode="json"), "artifact_id": "output",
                "schema_ref": expected.output_type.schema_ref.model_dump(mode="json")}}}})))
    return SimpleNamespace(env=env, record=record, evidence=receipt, params=params, deadline=deadline, entry=entry)


def audit(conn, fixture, revision):
    params = {**fixture.params, "revision": revision, "event": uuid.uuid4().hex}
    conn.execute(text("UPDATE runtime.runs SET revision=:revision WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run"), params)
    conn.execute(text("INSERT INTO runtime.audit_events(event_id,tenant_id,project_id,run_id,revision,ordinal,payload) "
                      "VALUES(:event,:tenant,:project,:run,:revision,0,'{}')"), params)
