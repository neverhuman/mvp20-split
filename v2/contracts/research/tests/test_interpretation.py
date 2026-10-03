"""Additive interpretation boundaries preserve weak evidence without accepting replacement verdicts."""
import json
from pathlib import Path

import amphora_contracts_research as contracts
import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

EXAMPLES = Path(__file__).absolute().parents[1]/"examples"
CASES = {
    "normalization-profile":contracts.NormalizationProfile,
    "observation-use-profile":contracts.ObservationUseProfile,
    "interpretation-profile-ref":contracts.InterpretationProfileRef,
    "normalize-observation-request":contracts.NormalizeObservationRequest,
    "assess-observation-use-request":contracts.AssessObservationUseRequest,
    "normalization-projection":contracts.NormalizationProjection,
    "observation-use-projection":contracts.ObservationUseProjection,
    "interpretation-ref":contracts.InterpretationRef,
}


@pytest.mark.parametrize("name,model",CASES.items())
def test_examples_roundtrip_and_both_schema_modes(name,model):
    payload = json.loads((EXAMPLES/(name+".json")).read_text())
    assert json.loads(model.model_validate_json(json.dumps(payload)).model_dump_json()) == payload
    for mode in ("validation","serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)


@pytest.mark.parametrize("name,field,value",[
    ("normalize-observation-request","result",{"status":"normalized"}),
    ("assess-observation-use-request","usable",[]),
    ("normalization-projection","authority","scientific_acceptance"),
    ("observation-use-projection","authority","runtime_acceptance"),
])
def test_requests_cannot_supply_verdicts_and_projections_cannot_promote_authority(name,field,value):
    model = CASES[name]
    payload = json.loads((EXAMPLES/(name+".json")).read_text()) | {field:value}
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(model.model_json_schema()).iter_errors(payload))


def test_use_output_exposes_weaknesses_without_a_campaign_verdict():
    row = contracts.ObservationUseProjection.model_validate_json((EXAMPLES/"observation-use-projection.json").read_text())
    review = row.reviews[0]
    assert review.disposition == "usable" and "controls_unknown" in review.focus
    assert review.observation.reference in row.usable and review.observation.reference in row.focus
    assert review.raw_match.reasons == ("readout_unit_mismatch",)
    assert review.effective_match.reasons == ()
    assert review.observation.value.quantity.value == "1.2500"
