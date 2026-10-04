import copy
import json
from pathlib import Path

import pytest
from amphora_contracts_planning import CampaignResearchSelection
from pydantic import ValidationError

FIXTURE = Path(__file__).parent / "fixtures/campaign-research-selection.json"


def test_finite_selection_roundtrip_and_frozen_collections():
    selection = CampaignResearchSelection.model_validate_json(FIXTURE.read_bytes())
    assert CampaignResearchSelection.model_validate_json(selection.model_dump_json()) == selection
    assert type(selection.questions) is tuple and type(selection.assessments) is tuple
    with pytest.raises(ValidationError):
        selection.assessments = ()


@pytest.mark.parametrize("variant", ["version", "authority", "question_bool", "assessment_hash",
                                      "assessment_revision", "query", "questions_limit", "needs_limit",
                                      "assessments_limit"])
def test_closed_selection_shape(variant):
    value = json.loads(FIXTURE.read_bytes())
    if variant == "version":
        value["schema_version"] = "2"
    elif variant == "authority":
        value["scientifically_accepted"] = True
    elif variant == "question_bool":
        value["questions"][0]["revision"] = True
    elif variant == "assessment_hash":
        value["assessments"][0]["status_sha256"] = "unknown"
    elif variant == "assessment_revision":
        value["assessments"][0]["revision"] = 1
    elif variant == "query":
        value["query"] = "SELECT * FROM research.questions"
    else:
        key = variant.removesuffix("_limit")
        value[key] = [copy.deepcopy(value[key][0])] * (33 if key == "assessments" else 65)
    with pytest.raises(ValidationError):
        CampaignResearchSelection.model_validate_json(json.dumps(value))


def test_empty_selection_is_explicit_and_shape_does_not_grant_identity():
    value = json.loads(FIXTURE.read_bytes())
    for field in ("questions", "needs", "assessments"):
        value[field] = []
    assert CampaignResearchSelection.model_validate_json(json.dumps(value)).questions == ()
    value["request_sha256"] = "f" * 64
    # Cross-record/request authority is deliberately outside the DTO.
    assert CampaignResearchSelection.model_validate_json(json.dumps(value)).request_sha256 == "f" * 64
