"""Reviewed bounds are consumed inputs, not authority supplied by the model."""

import base64
import copy
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.campaign_artifact_context import (
    ArtifactContextItem,
    ArtifactContextPlan,
    ArtifactContextProjection,
)
from amphora_agent_planning.campaign_decisions import (
    CampaignDecisionReview,
    DecisionDeclaration,
)
from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan

from ..campaign_context.test_selection import request
from ..campaign_output.test_output import output
from ..campaign_proposals.test_authored import candidate
from ..campaign_proposals.test_composition import documents, metadata
from ..campaign_proposals.test_evidence import inputs as research_inputs
from ..campaign_proposals.test_evidence import prepared
from ..campaign_proposals.test_prepared import source
from ..persistence.test_reservations import policy


def fixture(*, name='future', limits=None, change=None, declaration_change=None, entry_change=None, tools=False, research=None):
    original = source(name, extras=(('science', b'synthetic Research context', True),) if research is not None else ())
    raw = original.request.document().model_dump(mode='json')
    context = raw['context']
    pins = [{'kind': kind, 'identity': context[key]['artifact_id'], 'revision': '1', 'sha256': context[key]['sha256']}
            for kind, key in [('source', 'objective'), ('policy', 'policy')]]
    bounds = {'campaign_id': 'scalar', 'revision': 1, 'context': pins, 'max_nodes': 2, 'max_scopes': 1,
                  'max_depth': 0, 'max_iterations': 1, 'max_tool_timeout': 30, 'side_effects': ['pure']}
    bounds.update(limits or {})
    document = {'format': 'planning-campaign-decision.v1', 'declaration_artifact_id': 'decision',
                    'engagement': raw['reference'], 'objective': context['objective'], 'policy': context['policy'],
                    'runtime_cut': raw['runtime_cut'], 'allowed_actions': ['propose_campaign'], 'eligibility_context': 'synthetic-tests',
                    'future': bounds, 'adjustments': []}
    if name == 'adjustment':
        adjustment = output(name)['candidate']['changes'][0]
        document['future'] = None
        document['adjustments'] = [{'target': adjustment['target'], 'input_name': adjustment['input_name'],
            'previous_value_sha256': adjustment['previous_value_sha256'],
            'bounds': {'kind': 'numeric_range', 'scalar': 'number', 'unit': '1', 'minimum': 1.0, 'maximum': 2.0}}]
    if declaration_change:
        document = copy.deepcopy(document)
        declaration_change(document)
    declaration = DecisionDeclaration.from_bytes(json.dumps(document).encode())
    raw['decision_scope'] = declaration.sha256
    artifact = dict(context['objective'], artifact_id='decision', sha256=declaration.sha256,
                    size_bytes=len(declaration.canonical), media_type='text/plain')
    entry = {'artifact': artifact, 'role': 'constraint', 'required': True}
    if entry_change:
        entry_change(entry)
    context['entries'].append(entry)
    plan = ArtifactContextPlan.bind(request(raw))
    bodies = {row.document()['identity']['artifact_id']: base64.b64decode(row.document()['payload']['body_base64'])
              for row in original.slices}
    bodies['decision'] = declaration.canonical
    items = tuple(ArtifactContextItem.available(row, bodies[row.reference.artifact_id]) for row in plan.items)
    selected = CampaignSlicePlan.from_artifacts(ArtifactContextProjection.bind(plan, items))
    if tools:
        selected = metadata(selected)
    value = output(name)
    value['decision_scope'] = declaration.sha256
    if name == 'future':
        value['candidate']['definition']['context'] = pins
        if tools:
            value['candidate']['definition']['body'] = documents()[1]['candidate']['definition']['body']
    value['candidate']['expected_evidence'] = []
    value['unresolved'] = []
    if research is not None:
        selected, evidence = research_inputs(selected=selected, **research)
        value['candidate']['expected_evidence'] = evidence['candidate']['expected_evidence']
    if change:
        change(value)
    proposal = prepared(selected, value)
    return proposal, declaration, policy(proposal.attempt.request)


def test_original_visible_declaration_permits_only_a_proposal():
    proposal, declaration, budget = fixture()
    review = CampaignDecisionReview.bind(proposal, declaration, budget)
    assert review.next_step == 'compile_future_draft'
    assert review.declaration.sha256 == proposal.attempt.request.document().decision_scope
    assert {json.loads(key.identity)['artifact_id'] for key in review.read_set.keys} == {
        declaration.document().objective.artifact_id, declaration.document().policy.artifact_id, 'decision'}
    assert review.demand.accounting_units == 60


@pytest.mark.parametrize(('field', 'value', 'error'), [
    ('campaign_id', 'unauthorized', 'decision_future_identity'),
    ('revision', 2, 'decision_future_identity'),
    ('context', [], 'decision_future_context'),
])
def test_generated_definition_cannot_widen_reviewed_identity(field, value, error):
    values = fixture(change=lambda draft: draft['candidate']['definition'].update({field: value}))
    with pytest.raises(ValueError, match=error):
        CampaignDecisionReview.bind(*values)


def test_node_ceiling_is_enforced():
    values = fixture(limits={'max_nodes': 1})
    with pytest.raises(ValueError, match='decision_future_nodes'):
        CampaignDecisionReview.bind(*values)


@pytest.mark.parametrize('entry', [{'role': 'source'}, {'required': False}])
def test_declaration_must_be_an_original_required_constraint(entry):
    values = fixture(entry_change=lambda value: value.update(entry))
    with pytest.raises(ValueError, match='decision_declaration_entry'):
        CampaignDecisionReview.bind(*values)


def test_changed_declaration_cannot_replace_original_pin():
    proposal, declaration, budget = fixture()
    value = declaration.document().model_dump(mode='json')
    value['future']['max_nodes'] = 20
    replacement = DecisionDeclaration.from_bytes(json.dumps(value).encode())
    with pytest.raises(ValueError, match='decision_declaration_digest'):
        CampaignDecisionReview.bind(proposal, replacement, budget)


@pytest.mark.parametrize('raw', [b'{}', b'{"format":1,"format":2}', b'NaN', b'\xff', b'x' * 65537],
                         ids=['empty', 'duplicate', 'nonfinite', 'encoding', 'oversize'])
def test_malformed_declaration_never_becomes_authority(raw):
    with pytest.raises(ValueError):
        DecisionDeclaration.from_bytes(raw)


def test_permitted_adjustment_does_not_claim_runtime_application():
    review = CampaignDecisionReview.bind(*fixture(name='adjustment'))
    assert review.next_step == 'runtime_adjustment_unavailable'


@pytest.mark.parametrize(('proposed', 'error'), [
    ({'kind': 'number', 'value': 2.01, 'unit': '1'}, 'decision_adjustment_range'),
    ({'kind': 'number', 'value': 0.99, 'unit': '1'}, 'decision_adjustment_range'),
    ({'kind': 'number', 'value': 1.25, 'unit': 'K'}, 'decision_adjustment_type_or_unit'),
    ({'kind': 'integer', 'value': 1, 'unit': '1'}, 'decision_adjustment_type_or_unit'),
    ({'kind': 'boolean', 'value': True}, 'decision_adjustment_type_or_unit'),
])
def test_adjustments_cannot_expand_scalar_permissions(proposed, error):
    values = fixture(name='adjustment', change=lambda draft: draft['candidate']['changes'][0].update(proposed=proposed))
    with pytest.raises(ValueError, match=error):
        CampaignDecisionReview.bind(*values)


@pytest.mark.parametrize(('change', 'error'), [
    ({'input_name': 'pressure'}, 'decision_adjustment_target'),
    ({'previous_value_sha256': 'c' * 64}, 'decision_adjustment_previous'),
    ({'target': {'scope_path': ['inner'], 'node_id': 'evaluate'}}, 'decision_adjustment_target'),
])
def test_adjustments_are_bound_to_exact_authored_input(change, error):
    values = fixture(name='adjustment', change=lambda draft: draft['candidate']['changes'][0].update(change))
    with pytest.raises(ValueError, match=error):
        CampaignDecisionReview.bind(*values)


@pytest.mark.parametrize(('limits', 'error'), [
    ({'max_tool_timeout': 29}, 'decision_future_timeout'),
    ({'side_effects': ['external']}, 'decision_future_side_effect'),
])
def test_reviewed_tool_permissions_can_be_narrower_than_descriptor(limits, error):
    values = fixture(tools=True, limits=limits)
    with pytest.raises(ValueError, match=error):
        CampaignDecisionReview.bind(*values)


def test_descriptor_applicability_is_required_but_not_owner_eligibility():
    assert CampaignDecisionReview.bind(*fixture(tools=True)).next_step == 'compile_future_draft'
    values = fixture(tools=True, declaration_change=lambda value: value.update(eligibility_context='clinical-use'))
    with pytest.raises(ValueError, match='decision_tool_applicability'):
        CampaignDecisionReview.bind(*values)


@pytest.mark.parametrize(('limits', 'error'), [
    ({'max_scopes': 1, 'max_depth': 16, 'max_iterations': 10000}, 'decision_future_scopes'),
    ({'max_scopes': 10, 'max_depth': 0, 'max_iterations': 10000}, 'decision_future_depth'),
    ({'max_scopes': 10, 'max_depth': 16, 'max_iterations': 1}, 'decision_future_iterations'),
])
def test_nested_execution_has_reviewed_bounds(limits, error):
    values = fixture(limits=dict(limits, max_nodes=100), change=lambda value:
                     value['candidate']['definition'].update(body=candidate()['definition']['body']))
    with pytest.raises(ValueError, match=error):
        CampaignDecisionReview.bind(*values)


def test_enumerated_adjustment_values_are_exact():
    def enumeration(value):
        value['adjustments'][0]['bounds'] = {'kind': 'enumeration', 'values': [
            {'kind': 'number', 'value': 1.25, 'unit': '1'}]}
    values = fixture(name='adjustment', declaration_change=enumeration)
    assert CampaignDecisionReview.bind(*values).next_step == 'runtime_adjustment_unavailable'
    values = fixture(name='adjustment', declaration_change=enumeration,
                     change=lambda value: value['candidate']['changes'][0]['proposed'].update(value=1.5))
    with pytest.raises(ValueError, match='decision_adjustment_value'):
        CampaignDecisionReview.bind(*values)


@pytest.mark.parametrize(('change', 'error'), [
    (lambda value: value.update(allowed_actions=['abstain', 'abstain']), 'decision_declaration_actions'),
    (lambda value: value.update(future=None), 'decision_declaration_candidate_scope'),
    (lambda value: value['future']['context'][0].update(sha256='0' * 64), 'decision_context_root_pin'),
    (lambda value: value['future']['context'].append(value['future']['context'][0]), 'decision_context_duplicate'),
    (lambda value: value['future'].update(side_effects=['pure', 'pure']), 'decision_side_effect_duplicate'),
    (lambda value: value['objective']['scope'].update(project_id='foreign'), 'decision_declaration_scope'),
])
def test_malformed_reviewed_configuration_is_rejected(change, error):
    _, declaration, _ = fixture()
    value = declaration.document().model_dump(mode='json')
    change(value)
    with pytest.raises(ValueError, match=error):
        DecisionDeclaration.from_bytes(json.dumps(value).encode())


@pytest.mark.parametrize(('change', 'error'), [
    (lambda value: value.update(runtime_cut=None), 'decision_declaration_adjustment_cut'),
    (lambda value: value['adjustments'].append(value['adjustments'][0]), 'decision_duplicate_adjustment'),
    (lambda value: value['adjustments'][0]['bounds'].update(minimum=3.0), 'decision_numeric_range'),
])
def test_adjustment_declarations_must_be_unambiguous(change, error):
    _, declaration, _ = fixture(name='adjustment')
    value = declaration.document().model_dump(mode='json')
    change(value)
    with pytest.raises(ValueError, match=error):
        DecisionDeclaration.from_bytes(json.dumps(value).encode())


def test_review_revalidates_budget_and_does_not_widen_ceilings():
    proposal, declaration, budget = fixture()
    value = budget.document().model_dump(mode='json')
    value['limits']['max_input_tokens'] -= 1
    narrower = BudgetPolicy.from_bytes(json.dumps(value).encode())
    with pytest.raises(ValueError, match='budget_ceiling_exceeded'):
        CampaignDecisionReview.bind(proposal, declaration, narrower)
    with pytest.raises(ValueError, match='decision_budget_binding'):
        CampaignDecisionReview.bind(proposal, declaration, replace(budget, canonical=b' ' + budget.canonical))


@pytest.mark.parametrize('action', ['abstain', 'request_evidence'])
def test_nonexecution_actions_remain_explicit(action):
    def output_change(value):
        value.update(action=action, candidate=None)
        if action == 'request_evidence':
            value['evidence_requests'] = intents
    intents = []
    def change(value):
        intents.extend(value['candidate']['expected_evidence'])
        output_change(value)
    values = fixture(declaration_change=lambda value: value.update(allowed_actions=[action], future=None),
                     change=change, research={})
    review = CampaignDecisionReview.bind(*values)
    assert review.next_step == ('abstained' if action == 'abstain' else 'evidence_request')


@pytest.mark.parametrize('research', [{'posture': 'unknown'}, {'posture': 'contradicted'}, {'omitted': ('question', 'need', 'assessment')}])
def test_uncertain_science_is_preserved_through_combined_policy(research):
    review = CampaignDecisionReview.bind(*fixture(research=research))
    assert review.next_step == 'compile_future_draft'
    assert review.composition.evidence.proposal.output.document().scientific_authority == 'not_established'
    if 'omitted' in research:
        assert {finding.code for finding in review.composition.findings} == {'question_unavailable', 'need_unavailable', 'assessment_unavailable'}


@pytest.mark.parametrize(('change', 'error'), [
    (lambda value: value['engagement'].update(engagement_id='foreign'), 'decision_declaration_engagement'),
    (lambda value: value.update(runtime_cut=output('adjustment')['candidate']['cut']), 'decision_declaration_cut'),
    (lambda value: value.update(declaration_artifact_id='absent'), 'decision_declaration_entry'),
    (lambda value: value.update(allowed_actions=['abstain']), 'decision_action_not_permitted'),
])
def test_hash_valid_declaration_still_must_match_original_request(change, error):
    values = fixture(declaration_change=change)
    with pytest.raises(ValueError, match=error):
        CampaignDecisionReview.bind(*values)


def test_root_reference_cannot_be_substituted_even_with_valid_context_pin():
    def change(value):
        value['objective'] = dict(value['objective'], artifact_id='another-objective')
        value['future']['context'][0]['identity'] = 'another-objective'
    values = fixture(declaration_change=change)
    with pytest.raises(ValueError, match='decision_declaration_roots'):
        CampaignDecisionReview.bind(*values)


def test_noncanonical_declaration_object_is_rejected():
    proposal, declaration, budget = fixture()
    with pytest.raises(ValueError, match='decision_declaration_canonical'):
        CampaignDecisionReview.bind(proposal, replace(declaration, canonical=b' ' + declaration.canonical), budget)
