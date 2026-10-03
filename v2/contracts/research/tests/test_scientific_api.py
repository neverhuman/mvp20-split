"""Scientific requests select pinned sources; only authenticated producers supply bounded evidence."""
import hashlib
import json
from pathlib import Path

import amphora_contracts_research as contracts
import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

EXAMPLES = Path(__file__).absolute().parents[1]/"examples"
CASES = {
    "scientific-input-profile-ref":contracts.ScientificInputProfileRef,
    "eligibility-input-profile":contracts.EligibilityInputProfile,
    "synthesis-input-profile":contracts.SynthesisInputProfile,
    "scientific-assessment-request":contracts.ScientificAssessmentRequest,
    "synthetic-eligibility-report":contracts.SyntheticEligibilityReport,
    "synthetic-synthesis-report":contracts.SyntheticSynthesisReport,
    "scientific-assessment-status":contracts.ScientificAssessmentStatus,
    "scientific-publication-request":contracts.ScientificPublicationRequest,
    "scientific-publication-status":contracts.ScientificPublicationStatus,
    "scientific-impact-request":contracts.ScientificImpactRequest,
    "register-scientific-consumer":contracts.RegisterScientificConsumer,
    "scientific-consumers-request":contracts.ScientificConsumersRequest,
}


def example(name):
    return json.loads((EXAMPLES/(name+".json")).read_text())


@pytest.mark.parametrize("name,model",CASES.items())
def test_examples_roundtrip_and_both_published_schema_modes_validate(name,model):
    payload = example(name)
    assert json.loads(model.model_validate_json(json.dumps(payload)).model_dump_json()) == payload
    for mode in ("validation","serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)


@pytest.mark.parametrize("name",["scientific-assessment-request","scientific-publication-request"])
@pytest.mark.parametrize("field",["verdict","actor_id","policy","payload","issuer"])
def test_request_cannot_supply_owner_policy_actor_or_result_bytes(name,field):
    payload = example(name)|{field:"caller-choice"}
    model = CASES[name]
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(model.model_json_schema()).iter_errors(payload))


@pytest.mark.parametrize("kind",["eligibility","synthesis"])
def test_producer_schema_is_self_contained_and_cannot_promote_scientific_authority(kind):
    body = contracts.synthetic_scientific_report_schema_document(kind)
    assert hashlib.sha256(body).hexdigest() == contracts.synthetic_scientific_report_schema(kind).sha256
    schema = json.loads(body)
    assert "$id" not in schema
    name = "synthetic-"+kind+"-report"
    Draft202012Validator(schema).validate(example(name))
    invalid = example(name)|{"authority":"scientific"}
    with pytest.raises(ValidationError):
        CASES[name].model_validate_json(json.dumps(invalid))
    assert list(Draft202012Validator(schema).iter_errors(invalid))


def test_publication_status_excludes_domain_receipt():
    payload = example("scientific-publication-status")
    payload["outcome"]["receipt"] = {"purpose":"scientific"}
    with pytest.raises(ValidationError):
        contracts.ScientificPublicationStatus.model_validate_json(json.dumps(payload))


@pytest.mark.parametrize("count",[0,17])
def test_report_count_is_bounded_before_peer_resolution(count):
    payload = example("scientific-assessment-request")
    payload["reports"] *= count
    with pytest.raises(ValidationError):
        contracts.ScientificAssessmentRequest.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(contracts.ScientificAssessmentRequest.model_json_schema()).iter_errors(payload))


def test_pending_and_operational_failure_are_distinct_from_scientific_results():
    payload = example("scientific-assessment-status")|{"outcome":{"status":"pending"}}
    assert contracts.ScientificAssessmentStatus.model_validate_json(json.dumps(payload)).outcome.status == "pending"
    payload = example("scientific-publication-status")|{"outcome":{"status":"failed","code":"source_revoked","external_effects":"possible"}}
    assert contracts.ScientificPublicationStatus.model_validate_json(json.dumps(payload)).outcome.status == "failed"


def test_lab_publication_selection_cannot_include_a_replacement_report():
    payload = example("scientific-publication-request")
    scope = payload["target"]["reference"]["scope"]
    payload["target"] = {"kind":"lab-intake","scope":scope,"intake_id":"intake"}
    assert contracts.ScientificPublicationRequest.model_validate_json(json.dumps(payload)).target.kind == "lab-intake"
    payload["target"]["report"] = example("scientific-assessment-request")["reports"][0]
    with pytest.raises(ValidationError):
        contracts.ScientificPublicationRequest.model_validate_json(json.dumps(payload))
