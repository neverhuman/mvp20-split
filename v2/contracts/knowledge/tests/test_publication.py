import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_knowledge import (
    ReasoningPublicationRequest,
    ReasoningPublicationStatus,
    reasoning_artifact_schema,
    reasoning_artifact_schema_document,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

CASES = json.loads((Path(__file__).parent / "fixtures/publication.json").read_text())


@pytest.mark.parametrize("name,model", [("request", ReasoningPublicationRequest), ("published", ReasoningPublicationStatus)])
def test_independent_publication_fixture_and_schema(name, model):
    raw = CASES[name]
    parsed = model.model_validate_json(json.dumps(raw))
    assert parsed.model_dump(mode="json") == raw
    for mode in ("validation", "serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(raw)


@pytest.mark.parametrize("outcome", [{"status": "pending"},
    {"status": "failed", "code": "source_denied", "external_effects": "none"},
    {"status": "failed", "code": "publication_binding_mismatch", "external_effects": "possible"}])
def test_pending_failure_and_external_uncertainty_are_explicit(outcome):
    raw = {**CASES["published"], "outcome": outcome}
    assert ReasoningPublicationStatus.model_validate_json(json.dumps(raw)).model_dump(mode="json") == raw


@pytest.mark.parametrize("field,value", [("actor_id", "forged"), ("purpose", "scientific_acceptance"),
    ("result", {}), ("inputs", []), ("receipt", {}), ("wire_version", "2")])
def test_caller_selects_stored_result_without_supplying_authority(field, value):
    raw = {**CASES["request"], field: value}
    with pytest.raises(ValidationError):
        ReasoningPublicationRequest.model_validate_json(json.dumps(raw))


def test_scientific_acceptance_is_not_a_publication_outcome():
    raw = copy.deepcopy(CASES["published"])
    raw["outcome"]["status"] = "scientifically_accepted"
    with pytest.raises(ValidationError):
        ReasoningPublicationStatus.model_validate_json(json.dumps(raw))


def test_payload_profile_is_pinned_to_existing_result_shape_without_a_base_override():
    schema_path = Path(__file__).parents[2] / "schemas/v1/knowledge.reasoning-result.validation.json"
    # The immutable predecessor publication is independent of the new profile helper.
    document = json.loads(schema_path.read_text())
    document.pop("$id")
    expected = (json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    assert reasoning_artifact_schema_document() == expected
    reference = reasoning_artifact_schema()
    assert reference.schema_id == "knowledge.reasoning-result.payload" and reference.version == "1"
    assert reference.sha256 == hashlib.sha256(expected).hexdigest()
    assert len(expected) <= 65536
    result = json.loads((Path(__file__).parent / "fixtures/reasoning.json").read_text())["result"]
    Draft202012Validator(document).validate(result)
