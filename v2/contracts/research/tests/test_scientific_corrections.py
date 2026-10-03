"""Correction views and exact impact queries cannot express active campaign invalidation."""
import json
from pathlib import Path

import amphora_contracts_research as contracts
import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

EXAMPLES = Path(__file__).absolute().parents[1]/"examples"
CASES = {"observation-correction-view":contracts.ObservationCorrectionView,
    "material-state-correction-view":contracts.MaterialStateCorrectionView,
    "material-state-impact-request":contracts.MaterialStateImpactRequest,
    "interpretation-impact-request":contracts.InterpretationImpactRequest,
    "interpretation-impact-page":contracts.InterpretationImpactPage}


@pytest.mark.parametrize("name,model",CASES.items())
def test_examples_roundtrip_in_both_schema_modes(name,model):
    payload = json.loads((EXAMPLES/(name+".json")).read_text())
    assert json.loads(model.model_validate_json(json.dumps(payload)).model_dump_json()) == payload
    for mode in ("validation","serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)


@pytest.mark.parametrize("name",["observation-correction-view","material-state-correction-view","interpretation-impact-page"])
def test_views_cannot_invalidate_active_campaigns(name):
    payload = json.loads((EXAMPLES/(name+".json")).read_text())|{"policy":"invalidate_active"}
    with pytest.raises(ValidationError):
        CASES[name].model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(CASES[name].model_json_schema()).iter_errors(payload))


@pytest.mark.parametrize("name",["material-state-impact-request","interpretation-impact-request"])
@pytest.mark.parametrize("limit",[0,129,True])
def test_impact_queries_are_explicitly_bounded(name,limit):
    payload = json.loads((EXAMPLES/(name+".json")).read_text())|{"limit":limit}
    with pytest.raises(ValidationError):
        CASES[name].model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(CASES[name].model_json_schema()).iter_errors(payload))
