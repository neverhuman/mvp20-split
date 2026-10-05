"""Named QEV scenarios exercise combined proposal policy, not live-model quality."""

import copy
import json

import pytest
from amphora_agent_planning.campaign_authoring import AuthoringPlan
from amphora_agent_planning.campaign_decisions import CampaignDecisionReview
from amphora_agent_planning.campaign_eligibility import (
    EligibilityBatch,
    EligibilityConfiguration,
    EligibilityObservation,
)

from ..campaign_decisions.test_policy import fixture
from ..campaign_eligibility.test_observations import NOW, response
from ..campaign_output.test_output import output
from ..campaign_refresh.test_collection import inputs


def focus(value):
    value['candidate']['expected_evidence'][0]['producer'] = {'scope_path': [], 'node_id': 'calculate'}
    value['unresolved'] = output()['unresolved']
    value['unresolved'].append({'question': None, 'need': None, 'posture': 'contradictory',
        'description': 'An independent earlier result remains questionable; revisit in a later campaign.'})


@pytest.mark.parametrize('research', [{'omitted': ('assessment',)}, {'posture': 'unknown'}, {'posture': 'contradicted'}],
                         ids=['missing-measurement', 'unknown', 'contradictory'])
def test_qev09_bounded_tool_proposal_preserves_multiple_unresolved_points(research):
    proposal, declaration, budget = fixture(tools=True, research=research, change=focus)
    original_packet, original_output = proposal.inputs.preparation.packet.canonical, proposal.observation.canonical
    review = CampaignDecisionReview.bind(proposal, declaration, budget)
    assert review.next_step == 'compile_future_draft'
    candidate = proposal.output.document().candidate
    intent = candidate.expected_evidence[0]
    assert intent.question.question_id == 'question-1' and intent.needs[0].need_id == 'need-1'
    assert intent.producer.node_id == 'calculate' and intent.expected_evidence and intent.uncertainty
    assert len(candidate.definition.body.nodes) == declaration.document().future.max_nodes == 2
    use = review.composition.uses[0]
    assert use.address == intent.producer
    selected = use.release.record.document()
    assert candidate.definition.body.inputs[0].value_type.schema_ref == selected.descriptor.tool.inputs[0].schema_ref
    config = EligibilityConfiguration.bind(owner_id='registry-fixture', actor_id='planning-agent', policy_sha256='e' * 64)
    batch = EligibilityBatch.bind(review, budget, config, 'qev09')
    observed = EligibilityObservation.bind(batch.requests[0], response(batch.requests[0]))
    observed.require_fresh(NOW)
    authoring = AuthoringPlan.bind(review, budget, owner_id='runtime-fixture', actor_id='planning-agent')
    assert authoring.save().payload().definition == candidate.definition
    retained = proposal.output.document()
    assert retained.authority == 'proposal_only' and retained.scientific_authority == 'not_established'
    assert [point.posture for point in retained.unresolved] == ['unknown', 'contradictory']
    assert proposal.inputs.preparation.packet.canonical == original_packet and proposal.observation.canonical == original_output
    if 'omitted' in research:
        assert 'assessment_unavailable' in {finding.code for finding in review.composition.findings}
    else:
        assessment = review.composition.evidence.research.context.records[-1].document()
        assert not assessment.outcome.assessment.scientifically_established


@pytest.mark.parametrize('posture', ['ineligible', 'unreviewed'])
def test_qev10_compatible_description_and_ports_cannot_override_scientific_ineligibility(posture):
    proposal, declaration, budget = fixture(tools=True, research={'omitted': ('assessment',)}, change=focus)
    review = CampaignDecisionReview.bind(proposal, declaration, budget)
    config = EligibilityConfiguration.bind(owner_id='registry-fixture', actor_id='planning-agent', policy_sha256='e' * 64)
    request = EligibilityBatch.bind(review, budget, config, 'qev10').requests[0]
    original = proposal.inputs.preparation.packet.canonical
    def ineligible(value):
        value['decision']['observations']['scientific'].update(status=posture, reason_codes=['fixture-mismatch'])
    # Even an otherwise positive receipt with matching release, ports, healthy
    # capacity and allowed admission cannot contradict scientific ineligibility.
    contradictory = response(request, change=ineligible)
    with pytest.raises(ValueError, match='eligibility_positive_statuses'):
        EligibilityObservation.bind(request, contradictory)
    rejected = response(request, change=lambda value: value.update(status='rejected', reason_code='scientific_ineligible'))
    retained = EligibilityObservation.bind(request, rejected)
    assert retained.status == 'rejected' and retained.receipt.reason_code == 'scientific_ineligible'
    with pytest.raises(ValueError, match='eligibility_rejected'):
        retained.require_fresh(NOW)
    assert proposal.inputs.preparation.packet.canonical == original
    assert len(proposal.output.document().unresolved) == 2


@pytest.mark.parametrize('relevant', [True, False], ids=['selected-criteria', 'unrelated-criteria'])
def test_qev11_changed_criteria_only_affect_the_selected_proposal(relevant):
    plan, collector, _, research, *_ = inputs(tools=True, research={'additional_question': True}, change=focus)
    key = next(key for key in research.records if key.kind == 'question' and
               (json.loads(key.reference)['question_id'] == 'another-question') != relevant)
    original = research.records[key]
    changed = copy.deepcopy(original.model_dump(mode='json'))
    changed['criteria'][0]['description'] = 'A newly narrowed synthetic observation requirement.'
    research.records[key] = type(original).model_validate_json(json.dumps(changed))
    before = plan.review.composition.evidence.proposal.inputs.preparation.packet.canonical
    result = collector.collect(plan)
    assert result.ready_for_preparation is not relevant
    assert len(result.changes) == int(relevant)
    if relevant:
        assert result.changes[0].before_sha256 != result.changes[0].after_sha256
    assert not result.latest_research_head_verified
    assert plan.review.composition.evidence.proposal.inputs.preparation.packet.canonical == before
    assert len(plan.review.composition.evidence.proposal.output.document().unresolved) == 2
