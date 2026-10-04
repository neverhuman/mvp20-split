"""Versioned strict edit shapes; this tier grants no accepted graph authority."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_planning import (
    ExtractionDraft,
    ExtractionDraftV2,
    ExtractionTask,
    ExtractionTaskV2,
    extraction_edit_schema,
)
from pydantic import ValidationError


def fixture():
    return json.loads((Path(__file__).parent / "fixtures/extraction-edits.json").read_bytes())


def test_explicit_edit_targets_roundtrip_separately_from_legacy_contract():
    value = fixture()
    task = ExtractionTaskV2.model_validate_json(json.dumps(value["task"]))
    draft = ExtractionDraftV2.model_validate_json(json.dumps(value["draft"]))
    assert task.schema_version == draft.schema_version == "2"
    assert len(task.existing_assertions) == 2
    assert [edit.operation for edit in draft.edits] == [
        "correct_assertion", "retract_assertion", "merge_entities", "revise_entity_context"]
    assert draft.entities[0].context is None and draft.assertions[0].posture == "unresolved"
    assert ExtractionTaskV2.model_validate_json(task.model_dump_json()) == task
    assert ExtractionDraftV2.model_validate_json(draft.model_dump_json()) == draft
    for model, document in ((ExtractionTask, task), (ExtractionDraft, draft)):
        with pytest.raises(ValidationError):
            model.model_validate_json(document.model_dump_json())
    schema = ExtractionDraftV2.model_json_schema(mode="validation")
    schema.update({'$schema': 'https://json-schema.org/draft/2020-12/schema',
                   '$id': 'urn:amphora:planning.extraction-edit-draft:1:validation'})
    content = (json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode()
    assert extraction_edit_schema().sha256 == hashlib.sha256(content).hexdigest()


@pytest.mark.parametrize('case', ['operation', 'authority', 'missing-target', 'missing-replacement',
    'missing-attribution', 'loose-revision', 'too-many', 'missing-context', 'missing-edits', 'old-version'])
def test_invalid_or_implicit_edits_fail_the_wire_boundary(case):
    draft = copy.deepcopy(fixture()['draft'])
    if case == 'operation':
        draft['edits'][0]['operation'] = 'execute_tool'
    elif case == 'authority':
        draft['edits'][0]['accepted'] = True
    elif case == 'missing-target':
        del draft['edits'][0]['prior']
    elif case == 'missing-replacement':
        del draft['edits'][0]['replacement_local_id']
    elif case == 'missing-attribution':
        del draft['edits'][0]['attribution']
    elif case == 'loose-revision':
        draft['edits'][0]['prior']['revision'] = True
    elif case == 'too-many':
        draft['edits'] *= 17
    elif case == 'missing-context':
        del draft['entities'][0]['context']
    elif case == 'missing-edits':
        del draft['edits']
    else:
        draft['schema_version'] = '1'
    with pytest.raises(ValidationError):
        ExtractionDraftV2.model_validate_json(json.dumps(draft))


def test_task_requires_explicit_bounded_assertion_selection():
    task = fixture()['task']
    del task['existing_assertions']
    with pytest.raises(ValidationError):
        ExtractionTaskV2.model_validate_json(json.dumps(task))
    task = fixture()['task']
    task['existing_assertions'] *= 65
    with pytest.raises(ValidationError):
        ExtractionTaskV2.model_validate_json(json.dumps(task))
