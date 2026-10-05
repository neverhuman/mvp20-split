"""Fresh candidate observations preserve specific eligibility and authority limits."""

import copy
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from amphora_agent_planning.campaign_decisions import CampaignDecisionReview
from amphora_agent_planning.campaign_eligibility import (
    EligibilityBatch,
    EligibilityConfiguration,
    EligibilityObservation,
)
from amphora_contracts_tools import RegistryReceipt

from ..campaign_decisions.test_policy import fixture

NOW = datetime(2026, 10, 4, 22, 0, tzinfo=UTC)


def batch(*, tools=True, check_id='check-1'):
    proposal, declaration, budget = fixture(tools=tools)
    review = CampaignDecisionReview.bind(proposal, declaration, budget)
    config = EligibilityConfiguration.bind(owner_id='registry-fixture', actor_id='planning-agent', policy_sha256='e' * 64)
    return EligibilityBatch.bind(review, budget, config, check_id)


@pytest.fixture(scope='module')
def selected():
    return batch()


def response(request, *, change=None):
    release = request.selected.document().model_dump(mode='json')
    release.update(status='active', revision=2)
    value = {'operation_id': 'resolution-1', 'status': 'accepted', 'reason_code': 'candidate',
        'release': release, 'deployment': None, 'heartbeat': None,
        'decision': {'observations': {'scope': release['scope'], 'release': release['lock'], 'policy_sha256': 'e' * 64,
            'structural': {'status': 'valid', 'findings': []},
            'scientific': {'status': 'eligible', 'reason_codes': []},
            'capacity': {'status': 'available', 'reason_codes': []}},
            'admission': {'status': 'allowed', 'reason_codes': ['synthetic-policy']}, 'status': 'candidate',
            'assessed_at': NOW.isoformat(), 'capacity_valid_until': (NOW + timedelta(seconds=30)).isoformat()}}
    # Deliberately independent nested identities for mutation oracles.
    value = json.loads(json.dumps(value))
    if change:
        change(value)
    return RegistryReceipt.model_validate_json(json.dumps(value))


def test_only_selected_release_is_resolved_under_original_context(selected):
    assert len(selected.requests) == 1
    request = selected.requests[0]
    payload = json.loads(request.command.canonical_bytes)['payload']
    assert payload['release'] == request.selected.document().lock.model_dump(mode='json')
    assert payload['context'] == selected.review.declaration.document().eligibility_context
    assert payload['inputs'] == [port.model_dump(mode='json') for port in request.selected.document().descriptor.tool.inputs]
    assert request.command.identity.actor_id == selected.configuration.document().actor_id
    assert request.verify() == request
    assert not batch(tools=False).requests


def test_same_check_replays_and_named_new_check_gets_a_new_identity(selected):
    same = EligibilityBatch.bind(selected.review, selected.budget, selected.configuration, selected.check_id)
    newer = EligibilityBatch.bind(selected.review, selected.budget, selected.configuration, 'check-2')
    assert same == selected
    assert newer.requests[0].command.identity != selected.requests[0].command.identity
    assert json.loads(newer.requests[0].command.canonical_bytes)['payload'] == json.loads(same.requests[0].command.canonical_bytes)['payload']


def test_positive_observation_is_finite_not_a_reservation(selected):
    request = selected.requests[0]
    observation = EligibilityObservation.bind(request, response(request))
    assert observation.status == 'candidate'
    assert observation.require_fresh(NOW) == observation
    assert observation.require_fresh(NOW + timedelta(seconds=5)) == observation
    assert observation.receipt.deployment is None and observation.receipt.heartbeat is None
    assert observation.request.configuration.document().policy_sha256 != selected.review.declaration.document().policy.sha256


@pytest.mark.parametrize('delta', [-0.001, 5.001, 30])
def test_future_old_and_expired_observations_are_not_fresh(selected, delta):
    request = selected.requests[0]
    observation = EligibilityObservation.bind(request, response(request))
    with pytest.raises(ValueError, match='eligibility_expired'):
        observation.require_fresh(NOW + timedelta(seconds=delta))


def test_capacity_expiry_can_be_stricter_than_maximum_age(selected):
    request = selected.requests[0]
    value = response(request, change=lambda value: value['decision'].update(capacity_valid_until=(NOW + timedelta(seconds=2)).isoformat()))
    observation = EligibilityObservation.bind(request, value)
    with pytest.raises(ValueError, match='eligibility_expired'):
        observation.require_fresh(NOW + timedelta(seconds=2))


@pytest.mark.parametrize(('change', 'error'), [
    (lambda v: v.update(reason_code='registered'), 'eligibility_response_shape'),
    (lambda v: v.update(decision=None), 'eligibility_response_shape'),
    (lambda v: v['release'].update(status='revoked'), 'eligibility_release_status'),
    (lambda v: v['release']['scope'].update(project_id='foreign'), 'registry_scope'),
    (lambda v: v['release']['lock']['tool'].update(image_sha256='f' * 64), 'registry_lock'),
    (lambda v: v['release']['descriptor']['tool'].update(purpose='Changed descriptor'), 'registry_lock'),
    (lambda v: v['decision']['observations']['scope'].update(project_id='foreign'), 'eligibility_observation_identity'),
    (lambda v: v['decision']['observations'].update(policy_sha256='f' * 64), 'eligibility_policy'),
    (lambda v: v['decision']['observations']['structural'].update(status='invalid'), 'eligibility_positive_statuses'),
    (lambda v: v['decision']['observations']['scientific'].update(status='unreviewed'), 'eligibility_positive_statuses'),
    (lambda v: v['decision']['observations']['capacity'].update(status='unknown'), 'eligibility_positive_statuses'),
    (lambda v: v['decision']['admission'].update(status='denied'), 'eligibility_positive_statuses'),
    (lambda v: v['decision'].update(status='rejected'), 'eligibility_positive_statuses'),
    (lambda v: v['decision'].update(capacity_valid_until=None), 'eligibility_expiry_window'),
    (lambda v: v['decision'].update(capacity_valid_until=NOW.isoformat()), 'eligibility_expiry_window'),
])
def test_mismatched_or_inconsistent_positive_receipts_never_grant_eligibility(selected, change, error):
    request = selected.requests[0]
    with pytest.raises(ValueError, match=error):
        EligibilityObservation.bind(request, response(request, change=change))


def test_explicit_rejection_is_retained_without_promoting_ancillary_fields(selected):
    request = selected.requests[0]
    receipt = response(request, change=lambda value: value.update(status='rejected', reason_code='no_capacity'))
    observation = EligibilityObservation.bind(request, receipt)
    assert observation.status == 'rejected' and observation.receipt.reason_code == 'no_capacity'
    with pytest.raises(ValueError, match='eligibility_rejected'):
        observation.require_fresh(NOW)


def test_derived_request_configuration_and_observation_cannot_be_forged(selected):
    request = selected.requests[0]
    with pytest.raises(ValueError, match='eligibility_request_binding'):
        replace(request, check_id='other').verify()
    with pytest.raises(ValueError, match='eligibility_configuration_binding'):
        replace(selected.configuration, canonical=b' ' + selected.configuration.canonical).verify()
    observation = EligibilityObservation.bind(request, response(request))
    with pytest.raises(ValueError, match='eligibility_observation_binding'):
        replace(observation, status='accepted').require_fresh(NOW)
    with pytest.raises(ValueError, match='eligibility_clock'):
        observation.require_fresh(NOW.replace(tzinfo=None))


@pytest.mark.parametrize('age', [0, 61, True])
def test_configuration_age_is_bounded(age):
    with pytest.raises(ValueError):
        EligibilityConfiguration.bind(owner_id='registry', actor_id='actor', policy_sha256='e' * 64, maximum_age_seconds=age)


def test_repeated_tool_invocations_share_one_exact_eligibility_check(selected):
    def change(value):
        body = value['candidate']['definition']['body']
        another = copy.deepcopy(body['nodes'][0])
        another['node_id'] = 'calculate-again'
        body['nodes'].insert(1, another)
        body['nodes'][-1]['outputs'][0]['source']['node_id'] = 'calculate-again'
        body['edges'] = [{'source': 'calculate', 'target': 'calculate-again', 'route': 'next'},
                         {'source': 'calculate-again', 'target': 'finish', 'route': 'next'}]
    proposal, declaration, budget = fixture(tools=True, limits={'max_nodes': 3}, change=change)
    review = CampaignDecisionReview.bind(proposal, declaration, budget)
    result = EligibilityBatch.bind(review, budget, selected.configuration, 'twice')
    assert len(review.composition.uses) == 2 and len(result.requests) == 1
    assert result.verify() == result
    with pytest.raises(ValueError, match='eligibility_batch_binding'):
        replace(result, requests=()).verify()


def test_review_and_original_context_cannot_be_replaced(selected):
    with pytest.raises(ValueError, match='eligibility_review_binding'):
        EligibilityBatch.bind(replace(selected.review, next_step='abstained'), selected.budget,
                              selected.configuration, selected.check_id)
    with pytest.raises(ValueError, match='eligibility_context'):
        replace(selected.requests[0], context='clinical').verify()
