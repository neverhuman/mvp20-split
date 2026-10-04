"""Fresh-process family enrollment, pending reservation recovery and exact replay."""

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.persistence.repair import RepairJournal
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.capture import Observation, unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_core import Scope
from sqlalchemy import create_engine


def main():
    stage, project = sys.argv[1:]
    exposure = stage.startswith("overage_")
    if exposure:
        project += "-overage"
    for peer in ("amphora_knowledge", "amphora_research", "amphora_data_artifacts", "amphora_runtime"):
        assert importlib.util.find_spec(peer) is None
    raw = json.loads((Path(__file__).parents[1] / "extraction/fixtures/extraction.json").read_bytes())
    scope = Scope(tenant_id="planning-repair-family", project_id=project)
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {"tenant_id", "project_id"}:
                value.update(scope.model_dump())
            for item in value.values():
                rescope(item)
        elif isinstance(value, list):
            for item in value:
                rescope(item)
    rescope(raw)
    raw["request"]["context"]["limits"].update(max_attempts=3 if exposure else 2, total_tokens=100000, total_accounting_units=1000)
    def task(name):
        request = json.loads(json.dumps(raw["request"]))
        request["reference"]["engagement_id"] = name
        snapshot = RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id="fixture", scope=scope)
        document = dict(raw["task"], task_id=name, engagement=request["reference"], request_sha256=snapshot.sha256)
        return ExtractionSnapshot.from_bytes(json.dumps(document).encode(), snapshot)
    root, child, extra = task("root"), task("child"), task("extra")
    context = root.request.document().context.model_dump(mode="json")
    policy = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=40)
    policy = BudgetPolicy.from_bytes(json.dumps(policy).encode())
    calls = []
    class Provider:
        def supports(self, model): return True
        def reply(self, binding):
            name = binding.request.document().reference.engagement_id
            calls.append(name)
            assert name != "extra"
            return ProviderReply((b"{" if name == "root" else json.dumps(raw["draft"]).encode(),), unknown_usage())
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"], connect_args={"options": "-c statement_timeout=5000"})
    try:
        runner, traces, families = PlanningRunner(engine, Provider(), timeout_seconds=30), ExtractionJournal(engine), RepairJournal(engine)
        for candidate in (root, child, extra):
            runner.journal.register(principal, candidate.request)
            traces.register(principal, candidate)
        root_member = families.enroll_root(principal, "root", policy)
        root_binding = AttemptBinding(root.request, 1)
        runner.execute(principal, root_binding, policy)
        parent = traces.record(principal, "root", root_binding.reference(), "parent")
        child_member = families.enroll_child(principal, root.document().engagement, "child", parent.projection.reference())
        child_binding = AttemptBinding(child.request, 1)
        reservation = runner.ledger.reserve(principal, child_binding, policy)
        if exposure:
            families.enroll_child(principal, root.document().engagement, "extra", parent.projection.reference())
            extra_binding = AttemptBinding(extra.request, 1)
            runner.ledger.reserve(principal, extra_binding, policy)
            if stage == "overage_write":
                ticket = runner.dispatch.issue(principal, child_binding, 30)
                observed = observe(child_binding, Provider())
                wire = observed.document().model_dump(mode="json")
                wire["usage"]["accounting_units"] = 9999
                runner.dispatch.complete(principal, child_binding, ticket, Observation(observed.capture, json.dumps(wire).encode()))
            current = runner.journal.read_attempt(principal, child_binding.reference())
            assert current.observation.document().usage.accounting_units == 9999
            assert runner.settlements.read(principal, child_binding.reference()) is None
            try:
                runner.dispatch.issue(principal, extra_binding, 30)
            except ValueError as exc:
                assert str(exc) == "provider_usage_overage"
            else:
                raise AssertionError("unsettled sibling overage admitted a call")
            assert calls == (["root", "child"] if stage == "overage_write" else [])
            print(json.dumps({"pid": os.getpid(), "calls": calls, "observation_sha256": hashlib.sha256(current.observation.canonical).hexdigest(),
                "reservation_at": reservation.registered_at.isoformat(), "settlement": None, "blocked": "provider_usage_overage"}))
            return
        records = [parent]
        if stage in {"run", "replay"}:
            runner.execute(principal, child_binding, policy)
            records.append(traces.record(principal, "child", child_binding.reference(), "child-trace", parent.projection.reference()))
        families.enroll_child(principal, root.document().engagement, "extra", parent.projection.reference())
        blocked = runner.run(principal, extra.request, policy)
        assert blocked.stop_reason == "repair_attempt_budget_exhausted" and not blocked.attempts
        assert calls == {"prepare": ["root"], "run": ["child"], "replay": []}[stage]
        assert families.read(principal, root.document().engagement) == root_member
        assert families.read(principal, child.document().engagement) == child_member
        print(json.dumps({"pid": os.getpid(), "calls": calls, "blocked": blocked.stop_reason,
            "root": {"sha256": hashlib.sha256(root_member.canonical).hexdigest(), "registered_at": root_member.registered_at.isoformat()},
            "child": {"sha256": hashlib.sha256(child_member.canonical).hexdigest(), "registered_at": child_member.registered_at.isoformat()},
            "reservation_at": reservation.registered_at.isoformat(),
            "traces": [{"sha256": row.projection.sha256, "recorded_at": row.recorded_at.isoformat(),
                        "charge": runner.settlements.read(principal, row.projection.document().attempt).charge.accounting_units}
                       for row in records]}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
