"""Additive synthetic documents have strict wire shapes and no implicit execution authority."""
import json
from pathlib import Path

import pytest
from amphora_contracts_research import (
    EligibilityAssessment,
    EligibilityProfile,
    ExperimentDefinition,
    MaterialStateRevision,
    ObservationRevision,
    SynthesisAssessment,
    SynthesisProfile,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

EXAMPLES = Path(__file__).absolute().parents[1] / "examples"
DOCUMENTS = (("material-state-revision",MaterialStateRevision),("experiment-definition",ExperimentDefinition),
             ("observation-revision",ObservationRevision),("synthesis-profile",SynthesisProfile),
             ("synthesis-assessment",SynthesisAssessment),("eligibility-profile",EligibilityProfile),
             ("eligibility-assessment",EligibilityAssessment))


@pytest.mark.parametrize("name,model",DOCUMENTS)
def test_document_examples_roundtrip_with_both_schema_modes(name,model):
    payload = json.loads((EXAMPLES / (name+".json")).read_text(encoding="utf-8"))
    result = model.model_validate_json(json.dumps(payload))
    assert json.loads(result.model_dump_json()) == payload
    for mode in ("validation","serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)


@pytest.mark.parametrize("name,model",DOCUMENTS)
def test_transport_shape_cannot_add_acceptance_authority(name,model):
    payload = json.loads((EXAMPLES / (name+".json")).read_text(encoding="utf-8"))
    payload["runtime_accepted"] = True
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(model.model_json_schema()).iter_errors(payload))


@pytest.mark.parametrize("name,model",DOCUMENTS[3:])
def test_synthetic_document_cannot_claim_scientific_authority(name,model):
    payload = json.loads((EXAMPLES / (name+".json")).read_text(encoding="utf-8"))
    payload["authority"] = "scientific"
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(model.model_json_schema()).iter_errors(payload))


def test_optional_requirement_is_not_coerced_from_a_number():
    payload = json.loads((EXAMPLES / "eligibility-profile.json").read_text(encoding="utf-8"))
    payload["requirements"][0]["required"] = 1
    with pytest.raises(ValidationError):
        EligibilityProfile.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(EligibilityProfile.model_json_schema()).iter_errors(payload))


def test_examples_preserve_failed_route_and_unknown_optional_point():
    synthesis = SynthesisAssessment.model_validate_json((EXAMPLES / "synthesis-assessment.json").read_text(encoding="utf-8"))
    assert [item.disposition for item in synthesis.alternatives] == ["blocked","eligible"]
    eligibility = EligibilityAssessment.model_validate_json((EXAMPLES / "eligibility-assessment.json").read_text(encoding="utf-8"))
    assert eligibility.disposition == "eligible" and eligibility.focus == ("accuracy",)
    assert eligibility.criteria[1].disposition == "unknown"
