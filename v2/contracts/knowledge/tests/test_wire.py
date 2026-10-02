"""Independent shape oracles; accepted fixture hashes are placeholders, not receipts."""

import copy
import json
from pathlib import Path

import pytest
from amphora_contracts_knowledge import (
    AcceptedGraphChange,
    DomainGraphSnapshot,
    DomainVocabulary,
    GraphAuthoringProfile,
    GraphChangeDecision,
    GraphChangeProposal,
    GraphProposalStatus,
)
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as SchemaError
from pydantic import ValidationError

CASES = json.loads((Path(__file__).parent / "fixtures/golden.json").read_text(encoding="utf-8"))
MODELS = {"vocabulary": DomainVocabulary, "proposal": GraphChangeProposal, "snapshot": DomainGraphSnapshot,
          "accepted": AcceptedGraphChange, "accepted_decision": GraphChangeDecision, "conflict_decision": GraphChangeDecision}


def parse(model, value):
    return model.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("origin", ["configured_default", "stored"])
def test_profile_discovery_preserves_explicit_origin(origin):
    proposal = CASES["proposal"]
    value = {"wire_version": "1", "graph": proposal["graph"], "vocabulary": CASES["vocabulary"],
        "vocabulary_reference": proposal["vocabulary"], "policy": proposal["policy"], "origin": origin}
    parsed = parse(GraphAuthoringProfile, value)
    assert parsed.model_dump(mode="json") == value
    for mode in ("validation", "serialization"):
        Draft202012Validator(GraphAuthoringProfile.model_json_schema(mode=mode)).validate(value)
    # DTO shape alone does not prove matching profile hashes; owner computes them.
    value["origin"] = "migrated_implicitly"
    with pytest.raises(ValidationError):
        parse(GraphAuthoringProfile, value)


@pytest.mark.parametrize("name", MODELS)
def test_fixture_roundtrip_and_json_schema(name):
    model, case = MODELS[name], CASES[name]
    parsed = parse(model, case)
    assert parse(model, parsed.model_dump(mode="json")) == parsed
    for mode in ("validation", "serialization"):
        validator = Draft202012Validator(model.model_json_schema(mode=mode))
        validator.validate(parsed.model_dump(mode="json"))


@pytest.mark.parametrize("operation", ["correct_assertion", "retract_assertion", "merge_entities", "revise_entity_context"])
def test_each_typed_edit_has_an_explicit_exact_target(operation):
    case = copy.deepcopy(CASES["proposal"])
    first, second, claim = [item.get("entity", item.get("assertion")) for item in case["operations"]]
    if operation == "correct_assertion":
        replacement = copy.deepcopy(claim)
        replacement["reference"]["revision"] = 2
        replacement["supersedes"] = claim["reference"]
        replacement["polarity"] = "negated"
        item = {"operation": operation, "prior": claim["reference"], "replacement": replacement}
    elif operation == "retract_assertion":
        item = {"operation": operation, "assertion": claim["reference"]}
    elif operation == "merge_entities":
        item = {"operation": operation, "source": first["reference"], "target": second["reference"]}
    else:
        replacement = copy.deepcopy(first)
        replacement["reference"]["revision"] = 2
        replacement["supersedes"] = first["reference"]
        item = {"operation": operation, "prior": first["reference"], "replacement": replacement}
    case["operations"] = [item]
    parsed = parse(GraphChangeProposal, case)
    assert parsed.operations[0].operation == operation
    assert parsed.model_dump(mode="json")["operations"] == [item]
    Draft202012Validator(GraphChangeProposal.model_json_schema()).validate(case)


@pytest.mark.parametrize("value", [0, -1, 1.5, "1", True, 9007199254740992])
def test_revision_shape_is_bounded_and_not_coerced(value):
    case = copy.deepcopy(CASES["proposal"])
    case["operations"][0]["entity"]["reference"]["revision"] = value
    with pytest.raises(ValidationError):
        parse(GraphChangeProposal, case)
    with pytest.raises(SchemaError):
        Draft202012Validator(GraphChangeProposal.model_json_schema()).validate(case)


@pytest.mark.parametrize("mutation", [
    lambda c: c.update(operations=[]),
    lambda c: c.update(operations=c["operations"] * 43),
    lambda c: c["operations"][0].update(operation="execute_tool"),
    lambda c: c.update(execute=True),
    lambda c: c["operations"][2]["assertion"].update(posture="scientifically_accepted"),
    lambda c: c["grounding"].update(spans=[]),
    lambda c: c["grounding"].update(conversion_traces=[]),
    lambda c: c["operations"][2]["assertion"]["research_links"][0].pop("need"),
], ids=["empty", "oversize", "unknown-op", "extra-authority", "scientific-promotion", "no-spans", "no-trace", "implicit-null"])
def test_invalid_proposal_shapes_fail_both_consumers(mutation):
    case = copy.deepcopy(CASES["proposal"])
    mutation(case)
    with pytest.raises(ValidationError):
        parse(GraphChangeProposal, case)
    with pytest.raises(SchemaError):
        Draft202012Validator(GraphChangeProposal.model_json_schema()).validate(case)


@pytest.mark.parametrize("outcome", ["accepted", "rejected", "conflict"])
def test_decision_payload_cannot_mix_success_and_failure(outcome):
    case = copy.deepcopy(CASES["accepted_decision"])
    case["decision"]["outcome"] = outcome
    case["decision"]["findings"] = CASES["conflict_decision"]["decision"]["findings"]
    with pytest.raises(ValidationError):
        parse(GraphChangeDecision, case)


def test_acceptance_authority_and_timezone_are_explicit():
    case = copy.deepcopy(CASES["accepted"])
    case["content"]["authority"] = "scientific"
    with pytest.raises(ValidationError):
        parse(AcceptedGraphChange, case)
    case["content"]["authority"] = "structural_only"
    case["content"]["accepted_at"] = "2026-10-01T23:00:01"
    with pytest.raises(ValidationError):
        parse(AcceptedGraphChange, case)


def test_valid_shape_is_not_a_scope_or_hash_authorization():
    # Semantic counterexample deliberately passes shape validation; the owner must reject it.
    case = copy.deepcopy(CASES["proposal"])
    case["operations"][0]["entity"]["reference"]["graph"]["scope"]["project_id"] = "foreign"
    parsed = parse(GraphChangeProposal, case)
    assert parsed.graph.scope != parsed.operations[0].entity.reference.graph.scope
    assert parse(AcceptedGraphChange, CASES["accepted"]).content.authority == "structural_only"


def test_frozen_record_does_not_erase_negation_or_hypothesis():
    case = copy.deepcopy(CASES["proposal"])
    case["operations"][2]["assertion"]["polarity"] = "negated"
    parsed = parse(GraphChangeProposal, case)
    claim = parsed.operations[2].assertion
    assert claim.polarity == "negated" and claim.posture == "hypothesis"
    assert claim.research_links[0].need.revision == 1
    with pytest.raises(ValidationError):
        claim.posture = "reported"


@pytest.mark.parametrize("decision", [None, CASES["accepted_decision"], CASES["conflict_decision"]])
def test_status_distinguishes_pending_and_terminal_shapes(decision):
    case = {"wire_version": "1", "proposal": CASES["proposal"], "actor_id": "reviewer",
            "request_sha256": "a"*64, "registered_at": "2026-10-01T23:00:00Z", "decision": decision}
    record = parse(GraphProposalStatus, case)
    assert (record.decision is None) == (decision is None)
    Draft202012Validator(GraphProposalStatus.model_json_schema()).validate(case)
    case.pop("decision")
    with pytest.raises(ValidationError):
        parse(GraphProposalStatus, case)
