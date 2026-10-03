"""Decision output and impact schemas preserve explicit authority and exact references."""
import json
from pathlib import Path

import pytest
from amphora_contracts_research import (
    DecisionConsumerPage,
    EligibilityDecision,
    ScientificDecisionRef,
    ScientificImpactPage,
    SynthesisDecision,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

EXAMPLES = Path(__file__).absolute().parents[1]/"examples"
CASES = (("scientific-decision-ref",ScientificDecisionRef),("eligibility-decision",EligibilityDecision),
         ("synthesis-decision",SynthesisDecision),("scientific-impact-page",ScientificImpactPage),
         ("decision-consumer-page",DecisionConsumerPage))


@pytest.mark.parametrize("name,model",CASES)
def test_public_examples_are_lossless_and_schema_valid(name,model):
    payload = json.loads((EXAMPLES/(name+".json")).read_text())
    assert json.loads(model.model_validate_json(json.dumps(payload)).model_dump_json()) == payload
    for mode in ("validation","serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)


@pytest.mark.parametrize("name,model",CASES)
def test_decision_outputs_cannot_claim_runtime_acceptance(name,model):
    payload = json.loads((EXAMPLES/(name+".json")).read_text())|{"runtime_accepted":True}
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(model.model_json_schema()).iter_errors(payload))


def test_impact_policy_cannot_be_changed_to_active_campaign_invalidation():
    payload = json.loads((EXAMPLES/"scientific-impact-page.json").read_text())|{"policy":"invalidate_active"}
    with pytest.raises(ValidationError):
        ScientificImpactPage.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(ScientificImpactPage.model_json_schema()).iter_errors(payload))
