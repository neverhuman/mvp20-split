import json
from pathlib import Path

import pytest
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.repair.binding import RepairRoot
from amphora_contracts_core import Scope

from ..persistence.test_reservations import policy


def bind(document):
    request = document["request"]
    snapshot = RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id=request["actor_id"],
        scope=Scope.model_validate(request["reference"]["scope"]))
    document["task"]["request_sha256"] = snapshot.sha256
    return ExtractionSnapshot.from_bytes(json.dumps(document["task"]).encode(), snapshot)


def inputs():
    document = json.loads((Path(__file__).parents[1] / "extraction/fixtures/extraction.json").read_bytes())
    document["request"]["context"]["entries"].append({"artifact": dict(document["request"]["context"]["objective"],
        artifact_id="original-result"), "role": "result", "required": True})
    task = bind(document)
    root = RepairRoot.bind(task, policy(task.request, units=10))
    document["request"]["reference"]["engagement_id"] = "child"
    document["task"]["engagement"]["engagement_id"] = "child"
    document["task"]["task_id"] = "child"
    return root, document


def test_narrowing_and_result_context_preserve_root_authority():
    root, document = inputs()
    context = document["request"]["context"]
    context["limits"]["max_attempts"] = 1
    context["allowed_actions"] = ["abstain"]
    artifact = dict(context["objective"], artifact_id="diagnostics")
    context["entries"].append({"artifact": artifact, "role": "result", "required": True})
    child = bind(document)
    assert root.validate_child(child) == child
    assert root.canonical == RepairRoot.bind(root.task, root.policy).canonical


@pytest.mark.parametrize("field", ["objective", "prompt", "policy"])
def test_exact_original_artifact_authority(field):
    root, document = inputs()
    document["request"]["context"][field]["artifact_id"] = "changed"
    with pytest.raises(ValueError, match="repair_context_authority"):
        root.validate_child(bind(document))


@pytest.mark.parametrize("change,reason", [
    ("decision", "repair_request_authority"), ("model", "repair_context_authority"),
    ("attempts", "repair_limits_exceeded"), ("tokens", "repair_limits_exceeded"),
    ("units", "repair_limits_exceeded"), ("context", "repair_context_added"),
    ("remove", "repair_context_removed"), ("target", "repair_task_pins"),
    ("questions", "repair_task_pins")])
def test_repair_cannot_expand_authority_or_change_pins(change, reason):
    root, document = inputs()
    request, task = document["request"], document["task"]
    context = request["context"]
    if change == "decision":
        request["decision_scope"] = "a" * 64
    if change == "model":
        context["model"]["model_revision"] = "other"
    if change == "attempts":
        context["limits"]["max_attempts"] += 1
    if change == "tokens":
        context["limits"]["total_tokens"] += 1
    if change == "units":
        context["limits"]["total_accounting_units"] += 1
    if change == "context":
        context["entries"].append({"artifact": dict(context["objective"], artifact_id="new-tool"), "role": "capability", "required": True})
    if change == "remove":
        context["entries"] = [entry for entry in context["entries"] if entry["role"] == "source"]
    if change == "target":
        task["target"]["graph"]["graph_id"] = "different"
    if change == "questions":
        task["known_questions"] = [{"scope": task["scope"], "question_id": "new", "revision": 1}]
    with pytest.raises(ValueError, match=reason):
        root.validate_child(bind(document))
