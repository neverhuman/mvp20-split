import copy
import json
from pathlib import Path

import pytest
from amphora_contracts_knowledge import ReasoningRequest, ReasoningResult, ReasoningRuleSet, ReasoningStatus
from jsonschema import Draft202012Validator
from pydantic import ValidationError

CASES = json.loads((Path(__file__).parent / "fixtures/reasoning.json").read_text())
MODELS = {"profile": ReasoningRuleSet, "request": ReasoningRequest, "result": ReasoningResult}


@pytest.mark.parametrize("name", MODELS)
def test_reasoning_roots_round_trip_with_schema_parity(name):
    model, value = MODELS[name], CASES[name]
    parsed = model.model_validate_json(json.dumps(value))
    assert parsed.model_dump(mode="json") == value
    for mode in ("validation", "serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(value)


@pytest.mark.parametrize("code", ["reasoning_work_limit", "reasoning_depth_limit", "reasoning_fact_limit"])
def test_incomplete_is_a_separate_outcome(code):
    value = copy.deepcopy(CASES["result"])
    value["outcome"] = {"status": "incomplete", "code": code}
    value["findings"][0]["status"] = "unknown"
    ReasoningResult.model_validate_json(json.dumps(value))
    Draft202012Validator(ReasoningResult.model_json_schema()).validate(value)


@pytest.mark.parametrize("outcome", [None, "evaluated", "failed"])
def test_durable_status_does_not_confuse_pending_and_terminal(outcome):
    decision = None
    if outcome == "failed":
        decision = {"outcome": "failed", "code": "peer_access_denied"}
    elif outcome == "evaluated":
        decision = {"outcome": "evaluated", "result": CASES["result"], "validation": {
            "checked_at": "2026-10-02T12:00:00Z", "artifacts": [], "sources": [],
            "conversion_traces": [], "questions": [], "evidence_needs": []}}
    value = {"wire_version": "1", "request": CASES["request"], "actor_id": "owner", "decision": decision}
    parsed = ReasoningStatus.model_validate_json(json.dumps(value))
    assert parsed.model_dump(mode="json") == value
    for mode in ("validation", "serialization"):
        Draft202012Validator(ReasoningStatus.model_json_schema(mode=mode)).validate(value)


@pytest.mark.parametrize("name,mutate", [
    ("profile", lambda v: v.update(authority="scientific_acceptance")),
    ("profile", lambda v: v["limits"].update(depth=True)),
    ("profile", lambda v: v["limits"].update(work=1_000_001)),
    ("profile", lambda v: v["limits"].update(facts=0)),
    ("profile", lambda v: v.update(execute="arbitrary_code")),
    ("request", lambda v: v.update(actor_id="injected")),
    ("request", lambda v: v.update(targets=[])),
    ("request", lambda v: v.update(targets=v["targets"] * 129)),
    ("request", lambda v: v["rule_set"].update(sha256="bad")),
    ("result", lambda v: v.update(authority="scientific_acceptance")),
    ("result", lambda v: v.update(findings=[])),
    ("result", lambda v: v.update(work=True)),
    ("result", lambda v: v.update(outcome={"status": "incomplete"})),
    ("result", lambda v: v["findings"][0].update(status="scientifically_established")),
])
def test_unbounded_or_authority_injecting_shapes_fail_both_validators(name, mutate):
    value = copy.deepcopy(CASES[name])
    mutate(value)
    model = MODELS[name]
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(value))
    assert list(Draft202012Validator(model.model_json_schema()).iter_errors(value))
