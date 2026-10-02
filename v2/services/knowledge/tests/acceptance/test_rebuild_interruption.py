"""Real process death with explicit barriers; original request is the retry authority."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from amphora_contracts_knowledge import CorrectAssertion
from amphora_knowledge.rebuild.store import RebuildStore
from amphora_knowledge.rebuild.workflow import RebuildWorkflow
from sqlalchemy import text

from ..persistence.test_ledger import observation
from .processes import Owner

pytestmark = pytest.mark.postgres


@pytest.fixture
def prepared(stored_graph, tmp_path):
    case = stored_graph
    case.principal = replace(case.principal, actions=case.principal.actions | {"rebuild_graph"})
    case.receipt = case.ledger.accept(case.principal, case.proposal, observation(case.proposal))
    case.store = RebuildStore(case.engine)
    RebuildWorkflow(case.store).run(case.principal, case.proposal.graph, "previous")
    config = {"database_url_env": "REBUILD_DATABASE", "principals": [{"token_env": "REBUILD_TOKEN",
        "actor_id": case.principal.actor_id, "scope": case.principal.scope.model_dump(), "actions": ["read_graph", "rebuild_graph"]}],
        "vocabulary": case.vocabulary.record.model_dump(mode="json"), "policy": case.policy.definition(),
        "data": {"endpoint": "http://127.0.0.1:1", "token_env": "REBUILD_TOKEN"},
        "research": {"endpoint": "http://127.0.0.1:1", "token_env": "REBUILD_TOKEN"}}
    case.config = tmp_path / "knowledge.json"
    case.config.write_text(json.dumps(config), encoding="utf-8")
    case.environment = dict(os.environ, REBUILD_DATABASE=case.engine.url.render_as_string(hide_password=False), REBUILD_TOKEN="k"*32)
    case.query = {"wire_version": "1", "graph": case.proposal.graph.model_dump(mode="json"), "rebuild_id": "interrupted"}
    return case


def pointer(case):
    with case.engine.connect() as connection:
        return connection.execute(text("SELECT rebuild_id FROM knowledge.snapshot_publications WHERE project_id=:project"),
            {"project": case.principal.scope.project_id}).scalar_one()


def evidence(case, name, details):
    root = Path(os.environ.get("AMPHORA_KNOWLEDGE_FAILURE_EVIDENCE", str(case.config.parent / "evidence")))
    root.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "scenario": name, "graph": case.proposal.graph.model_dump(mode="json"),
        "initial_head": case.receipt.decision.head.model_dump(mode="json"), "observed": details,
        "tier": "actual PostgreSQL and Knowledge HTTP process; accepted-input seeding is synthetic owner-local fixture"}
    (root / (name + ".json")).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


@pytest.mark.parametrize("stage", ["candidate_staged", "publication_before_result", "publication_committed"])
def test_kill_rebuild_reconciles_without_partial_publication(prepared, stage):
    case = prepared
    host = Owner("amphora_knowledge", case.config, case.environment, "k"*32, barrier=stage,
                 python=os.environ.get("AMPHORA_TEST_KNOWLEDGE_PYTHON"))
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            call = pool.submit(host.request, "/v1/graph-rebuilds", case.query)
            assert host.events.get(timeout=15) == {"barrier": stage}
            host.stop()
            assert call.exception(timeout=15) is not None
        status = case.store.status(case.principal, case.proposal.graph, "interrupted")
        committed = stage == "publication_committed"
        assert status.outcome == ("published" if committed else "pending")
        assert pointer(case) == ("interrupted" if committed else "previous")
        assert case.ledger.snapshot(case.principal, case.receipt.decision.head.snapshot) is not None
    finally:
        host.stop()
    replacement = Owner("amphora_knowledge", case.config, case.environment, "k"*32,
        python=os.environ.get("AMPHORA_TEST_KNOWLEDGE_REPLACEMENT_PYTHON"))
    try:
        result = replacement.request("/v1/graph-rebuilds", case.query)
        assert result["result"]["outcome"] == "published"
        assert result["result"]["head"] == case.receipt.decision.head.model_dump(mode="json")
        assert replacement.request("/v1/graph-rebuilds", case.query) == result
        assert replacement.request("/v1/graph-rebuilds/read", case.query) == result
        assert pointer(case) == "interrupted"
        evidence(case, stage, {"after_kill": status.outcome,
            "recovered": result, "pointer_after_recovery": "interrupted"})
    finally:
        replacement.stop()


def test_correction_during_private_build_cannot_be_overwritten(prepared):
    case = prepared
    host = Owner("amphora_knowledge", case.config, case.environment, "k"*32, barrier="candidate_staged",
                 python=os.environ.get("AMPHORA_TEST_KNOWLEDGE_PYTHON"))
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            call = pool.submit(host.request, "/v1/graph-rebuilds", case.query)
            assert host.events.get(timeout=15)["barrier"] == "candidate_staged"
            state = case.ledger._load_state(case.proposal.graph)
            prior = state.state.assertions.active()[0]
            corrected = prior.model_copy(update={"reference": prior.reference.model_copy(update={"revision": 2}),
                "supersedes": prior.reference, "polarity": "negated", "statement": "Correction must survive rebuild."})
            proposal = case.proposal.model_copy(update={"change_id": "correction", "base": state.head,
                "operations": (CorrectAssertion(operation="correct_assertion", prior=prior.reference, replacement=corrected),)})
            accepted = case.ledger.accept(case.principal, proposal, observation(proposal))
            assert accepted.decision.outcome == "accepted"
            assert pointer(case) == "previous"
            host.release()
            rebuilt = call.result(timeout=20)
        assert rebuilt["result"]["attempts"] == 2
        assert rebuilt["result"]["head"] == accepted.decision.head.model_dump(mode="json")
        snapshot = host.request("/v1/graph-snapshots/read", rebuilt["result"]["head"]["snapshot"])
        assert [item["polarity"] for item in snapshot["content"]["assertions"]] == ["affirmed", "negated"]
        assert snapshot["content"]["assertions"][1]["supersedes"] == prior.reference.model_dump(mode="json")
        evidence(case, "correction_race", {"rebuilt": rebuilt, "correction_head": accepted.decision.head.model_dump(mode="json"),
            "assertion_polarities": [item["polarity"] for item in snapshot["content"]["assertions"]]})
    finally:
        host.stop()
