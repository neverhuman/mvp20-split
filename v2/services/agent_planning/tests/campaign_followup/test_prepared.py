"""Production packet/capture reconstruction, without SQL or a physical model call."""

import copy
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_context import ResearchContext, ResearchSelection
from amphora_agent_planning.campaign_followup.output import FollowupOutput
from amphora_agent_planning.campaign_followup.policy import canonical
from amphora_agent_planning.campaign_followup.prepared import FollowupPreparation, PreparedFollowupProposal
from amphora_agent_planning.campaign_output import CampaignOutput
from amphora_agent_planning.campaign_preparations import CampaignPreparation
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.providers import observe
from amphora_contracts_planning import checkpoint_followup_draft_schema

from ..campaign_proposals.test_evidence import inputs
from ..campaign_proposals.test_prepared import record
from ..providers.test_task_output import Response
from .test_binding import output


def prepared_inputs(*, focus=False, assessed=True):
    selected, _ = inputs()
    prior = json.loads(next(row for row in selected.slices if row.lane == 'research').payload)
    original = selected.request.document().model_dump(mode='json')
    original['context']['output_schema'] = checkpoint_followup_draft_schema().model_dump(mode='json')
    request = RequestSnapshot.from_bytes(canonical(original), actor_id=original['actor_id'],
        scope=selected.request.document().reference.scope)
    value = prior['selection']
    value.update(schema_version='2', request_sha256=request.sha256, focus_artifact=None)
    groups = {'question': [], 'need': [], 'assessment': []}
    from amphora_agent_planning.campaign_context.records import RECORD_MODELS
    for row in prior['context']['records']:
        kind = row['identity']['kind']
        groups[kind].append(RECORD_MODELS[kind].model_validate_json(canonical(row['record'])))
    value['criteria'] = [{'question': copy.deepcopy(value['questions'][0]),
        'need': copy.deepcopy(value['needs'][0]), 'criterion_id': groups['need'][0].criterion_ids[0],
        'assessment': copy.deepcopy(value['assessments'][0]) if assessed else None}]
    if focus:
        value['focus_artifact'] = next(entry.artifact.model_dump(mode='json') for entry in
            request.document().context.entries if entry.artifact.artifact_id == 'science')
    selection = ResearchSelection.from_bytes(canonical(value), request)
    context = ResearchContext.bind(selection, questions=tuple(groups['question']), needs=tuple(groups['need']),
        assessments=tuple(groups['assessment']))
    selected = replace(selected, request=request, slices=tuple(row for row in selected.slices if row.lane != 'research'),
        families=tuple(name for name in selected.families if name != 'research')).with_research(context)
    preparation = record(selected)
    retained = FollowupPreparation.bind(preparation)
    draft = json.loads(json.dumps(output(retained.criteria)))
    draft['decision_scope'] = request.document().decision_scope
    draft['focus_artifact'] = value['focus_artifact']
    return selected, preparation, draft


def proposal(preparation, value):
    attempt = AttemptBinding(preparation.packet.request, 1)
    observation = observe(attempt, Response(canonical(value)))
    return PreparedFollowupProposal.bind(preparation, attempt, observation)


@pytest.mark.parametrize('focus,assessed', [(False, True), (False, False), (True, True)])
def test_retained_preparation_contains_exact_criteria_and_replays_without_owner_reads(focus, assessed):
    selected, preparation, value = prepared_inputs(focus=focus, assessed=assessed)
    restored = CampaignPreparation.from_bytes(selected.request, preparation.canonical, preparation.packet.canonical)
    result = proposal(restored, value)
    assert len(result.sha256) == 64
    assert result == proposal(preparation, value)
    rows = restored.packet.context()['slices']
    assert next(row for row in rows if row['lane'] == 'research')['payload']['selection']['criteria']
    assert result.output.document().scientific_authority == 'not_established'
    assert result.preparation.criteria.document().focus_artifact is not None if focus else True
    with pytest.raises(ValueError, match='campaign_output_profile'):
        CampaignOutput.parse(canonical(value), selected.request)


@pytest.mark.parametrize('case,code', [
    ('missing', 'followup_output_omitted'), ('foreign', 'followup_output_unselected'),
    ('changed_assessment', 'followup_output_unselected'), ('evidence', 'campaign_evidence_reference_unselected'),
    ('missing_research', 'followup_research_missing'), ('scope', 'followup_proposal_unavailable'),
    ('abstain_payload', 'followup_proposal_unavailable'),
])
def test_structural_capture_does_not_establish_retained_target_membership(case, code):
    selected, preparation, value = prepared_inputs()
    if case == 'missing': value.update(targets=[], unresolved=[])
    elif case == 'foreign': value['targets'][0]['criterion']['criterion_id'] = 'foreign'
    elif case == 'changed_assessment': value['targets'][0]['criterion']['assessment'] = None
    elif case == 'evidence': value['evidence_requests'][0]['question']['revision'] += 1
    elif case == 'scope': value['targets'][0]['criterion']['question']['scope']['project_id'] = 'foreign'
    elif case == 'abstain_payload': value['action'] = 'abstain'
    else:
        preparation = record(replace(selected, slices=tuple(row for row in selected.slices if row.lane != 'research'),
            families=tuple(name for name in selected.families if name != 'research')))
    with pytest.raises(ValueError, match=code):
        proposal(preparation, value)


def test_abstention_preserves_unresolved_and_tampering_cannot_change_fingerprint():
    _, preparation, value = prepared_inputs()
    value.update(action='abstain', targets=[], evidence_requests=[])
    result = proposal(preparation, value)
    assert result.observation.document().status == 'abstained'
    assert result.output.document().unresolved
    with pytest.raises(ValueError):
        _ = replace(result, output=replace(result.output, canonical=b'{}')).sha256
    raw = dict(value, decision_scope='f' * 64)
    with pytest.raises(ValueError, match='campaign_decision_scope'):
        FollowupOutput.parse(canonical(raw), preparation.packet.request)


def test_future_campaign_retains_criterion_intent_without_admission_or_execution():
    _, preparation, value = prepared_inputs()
    _, future = inputs()
    value.update(action='propose_campaign', candidate=future['candidate'], evidence_requests=[])
    result = proposal(preparation, value)
    assert result.output.document().candidate.kind == 'future_campaign'
    assert result.output.document().targets and result.output.document().unresolved
    assert len(result.sha256) == 64
