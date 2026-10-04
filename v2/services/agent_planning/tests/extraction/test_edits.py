"""Explicit v2 profile binding and retained interpretation, not edit acceptance."""

import copy
import hashlib
import json
from importlib.resources import files
from pathlib import Path

import pytest
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.extraction import (
    ExtractionSnapshot,
    PromptTemplate,
    SourceBundle,
    SourceText,
    TraceProjection,
)
from amphora_agent_planning.persistence.records import verified_observation
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.profiles import OutputProfiles
from amphora_contracts_core import Scope
from amphora_contracts_planning import extraction_draft_schema, extraction_edit_schema

from ..providers.test_task_output import Response


def documents(scope=None):
    value = json.loads((Path(__file__).parent / 'fixtures/extraction-edits.json').read_bytes())
    if scope is not None:
        def rescope(item):
            if isinstance(item, dict):
                if set(item) == {'tenant_id', 'project_id'}:
                    item.update(scope.model_dump())
                for child in item.values():
                    rescope(child)
            elif isinstance(item, list):
                for child in item:
                    rescope(child)
        rescope(value)
    request = RequestSnapshot.from_bytes(json.dumps(value['request']).encode(), actor_id='fixture',
                                         scope=Scope.model_validate(value['task']['scope']))
    value['task']['request_sha256'] = request.sha256
    task = ExtractionSnapshot.from_bytes(json.dumps(value['task']).encode(), request)
    return task, value


def test_v2_observation_trace_origins_and_prompt_pin_are_explicit():
    task, value = documents()
    binding = AttemptBinding(task.request, 1)
    capture = json.dumps(value['draft']).encode()
    observed = observe(binding, Response(capture))
    wire = observed.document()
    assert wire.schema_version == '2' and wire.status == 'proposed'
    assert wire.proposal.output_schema == extraction_edit_schema()
    assert verified_observation(binding, observed) == observed
    trace = TraceProjection.derive('edits', task, observed).document()
    assert trace.authority == 'interpretation_only' and trace.validation == 'profile_only'
    fields = {field.target_path: field for field in trace.fields}
    assert fields['/edits/0'].origin == 'model_inferred'
    assert fields['/edits/1'].origin == 'model_claimed_source'
    assert fields['/entities/0/context'].origin == 'missing'
    assert trace.outcome.candidate_sha256 == hashlib.sha256(wire.proposal.payload_json.encode()).hexdigest()
    source = SourceText.bind(task.document().sources[0], value['source_text'].encode())
    bundle = SourceBundle.bind(task, (source,))
    prompt_bytes = files('amphora_agent_planning.extraction').joinpath('prompts/domain-decomposition-v2.txt').read_bytes()
    prompt = PromptTemplate.bind(task.request.document().context.prompt, prompt_bytes)
    rendered = json.loads(prompt.render(task, bundle))
    assert rendered['profile'] == 'planning-extraction-input.v2'
    assert rendered['task']['existing_assertions'] == value['task']['existing_assertions']
    assert rendered['source_data'][0]['text'] == value['source_text']
    assert 'replacement_local_id' in rendered['trusted_instructions']


@pytest.mark.parametrize('case', ['foreign-assertion', 'other-graph', 'duplicate-assertion', 'missing-head', 'wrong-output'])
def test_task_selection_never_crosses_graph_or_profile(case):
    task, value = documents()
    if case == 'foreign-assertion':
        value['task']['existing_assertions'][0]['graph']['scope']['project_id'] = 'foreign'
    elif case == 'other-graph':
        value['task']['existing_assertions'][0]['graph']['graph_id'] = 'other'
    elif case == 'duplicate-assertion':
        value['task']['existing_assertions'].append(copy.deepcopy(value['task']['existing_assertions'][0]))
    elif case == 'missing-head':
        value['task']['target']['base'] = None
    else:
        value['request']['context']['output_schema'] = extraction_draft_schema().model_dump(mode='json')
        request = RequestSnapshot.from_bytes(json.dumps(value['request']).encode(), actor_id='fixture',
                                             scope=task.document().scope)
        value['task']['request_sha256'] = request.sha256
        task = type(task)(task.canonical, request)
    with pytest.raises(ValueError):
        ExtractionSnapshot.from_bytes(json.dumps(value['task']).encode(), task.request)


@pytest.mark.parametrize('case,status,reason', [
    ('foreign-edit', 'policy_rejected', 'proposal_scope_mismatch'),
    ('foreign-quote', 'policy_rejected', 'proposal_scope_mismatch'),
    ('unselected-context', 'policy_rejected', 'unselected_payload'),
    ('abstain-edits', 'invalid', 'abstention_payload'),
    ('legacy-draft', 'invalid', 'invalid_output'),
])
def test_v2_provider_boundary_does_not_grant_cross_scope_or_unselected_edits(case, status, reason):
    task, value = documents()
    draft = value['draft']
    if case == 'foreign-edit':
        draft['edits'][0]['prior']['graph']['scope']['project_id'] = 'foreign'
    elif case == 'foreign-quote':
        draft['edits'][0]['attribution']['quotations'][0]['span']['source']['scope']['project_id'] = 'foreign'
    elif case == 'unselected-context':
        draft['entities'][0]['context'] = task.request.document().context.objective.model_dump(mode='json')
    elif case == 'abstain-edits':
        draft['action'] = 'abstain'
        for group in ('entities', 'assertions', 'questions', 'answers', 'evidence_needs'):
            draft[group] = []
    else:
        draft['schema_version'] = '1'
    observation = observe(AttemptBinding(task.request, 1), Response(json.dumps(draft).encode())).document()
    assert observation.status == status and observation.reason_code == reason
    assert observation.proposal is None


def test_v1_profile_cannot_silently_interpret_v2_edits():
    task, value = documents()
    request = value['request']
    request['context']['output_schema'] = extraction_draft_schema().model_dump(mode='json')
    binding = AttemptBinding(RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id='fixture',
                             scope=task.document().scope), 1)
    result = observe(binding, Response(json.dumps(value['draft']).encode())).document()
    assert result.status == 'invalid' and result.reason_code == 'invalid_output'
    with pytest.raises(ValueError, match='unsupported_output_profile'):
        OutputProfiles.draft_model(extraction_edit_schema().model_copy(update={'sha256': 'f' * 64}))
