import copy
import json
from pathlib import Path

import pytest
from amphora_contracts_planning import ExtractionDraft, ExtractionTask, extraction_draft_schema
from pydantic import ValidationError


def fixture():
    return json.loads((Path(__file__).parent / "fixtures/extraction.json").read_bytes())


def test_public_task_and_draft_roundtrip_remain_candidates():
    value = fixture()
    task = ExtractionTask.model_validate_json(json.dumps(value["task"]))
    draft = ExtractionDraft.model_validate_json(json.dumps(value["draft"]))
    assert ExtractionTask.model_validate_json(task.model_dump_json()) == task
    assert ExtractionDraft.model_validate_json(draft.model_dump_json()) == draft
    assert isinstance(task.sources, tuple) and isinstance(draft.entities, tuple)
    assert draft.entities[0].attribution.origin == "source_stated"
    assert extraction_draft_schema().schema_id == "planning.extraction-draft"
    with pytest.raises(ValidationError):
        draft.action = "abstain"


@pytest.mark.parametrize("case", ["authority", "action", "confidence", "unit", "boolean-offset", "too-many"])
def test_wire_does_not_accept_authority_invented_actions_or_loose_counts(case):
    value = copy.deepcopy(fixture()["draft"])
    attribution = value["entities"][0]["attribution"]
    if case == "authority":
        value["accepted"] = True
    elif case == "action":
        value["action"] = "execute_code"
    elif case == "confidence":
        attribution["confidence"] = "scientifically_validated"
    elif case == "unit":
        attribution["quotations"][0]["span"]["unit"] = "character"
    elif case == "boolean-offset":
        attribution["quotations"][0]["span"]["start"] = True
    else:
        value["entities"] *= 65
    with pytest.raises(ValidationError):
        ExtractionDraft.model_validate_json(json.dumps(value))
