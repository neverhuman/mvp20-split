"""Pure prerequisite composition; owned-storage provenance has separate SQL tests."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from amphora_agent_planning.budget.charge import BudgetCharge
from amphora_agent_planning.campaign_authoring import AuthoringPlan
from amphora_agent_planning.campaign_eligibility import (
    EligibilityBatch,
    EligibilityConfiguration,
    EligibilityObservation,
)
from amphora_agent_planning.campaign_handoff import (
    CompilerPreparer,
    StoredCampaignOrigin,
)
from amphora_agent_planning.campaign_preparations.journal import (
    StoredCampaignPreparation,
)
from amphora_agent_planning.persistence.budget import BudgetReservation
from amphora_agent_planning.persistence.records import AttemptJournal
from amphora_agent_planning.persistence.settlement import BudgetSettlement

from ..campaign_eligibility.test_observations import NOW, response
from ..campaign_refresh.test_collection import inputs


def origin(review, budget):
    proposal = review.composition.evidence.proposal
    now = datetime.now(UTC)
    return StoredCampaignOrigin.bind(review, budget, StoredCampaignPreparation(proposal.inputs.preparation, now),
        AttemptJournal(proposal.attempt, proposal.observation), BudgetReservation(review.demand, now),
        BudgetSettlement(BudgetCharge.reconcile(review.demand, proposal.observation.canonical), now))


class ScriptedOrigin:
    def __init__(self, value):
        self.value, self.calls = value, 0

    def read(self, principal, review, budget):
        self.calls += 1
        return self.value


def fixture(*, tools=False, **kwargs):
    plan, collector, data, *_ = inputs(tools=tools, **kwargs)
    authoring = AuthoringPlan.bind(plan.review, plan.budget, owner_id='runtime', actor_id='planning-agent')
    configuration = EligibilityConfiguration.bind(owner_id='registry', actor_id='planning-agent', policy_sha256='e' * 64)
    batch = EligibilityBatch.bind(plan.review, plan.budget, configuration, 'check-1')
    observations = tuple(EligibilityObservation.bind(request, response(request)) for request in batch.requests)
    source = ScriptedOrigin(origin(plan.review, plan.budget))
    return CompilerPreparer(source, collector), authoring, batch, observations, data


def test_zero_tool_preparation_reads_origin_and_refreshes_without_registry_or_writes():
    preparer, authoring, batch, observations, data = fixture()
    result = preparer.prepare(None, authoring, batch, observations)
    assert result.status == 'ready_to_journal' and not result.observations
    assert preparer.origin.calls == 1 and data.calls
    assert result.origin.verify() == preparer.origin.value
    assert result.origin.settlement == preparer.origin.value.settlement


@pytest.mark.parametrize('state', ['candidate', 'rejected', 'expired'])
def test_exact_tool_outcomes_have_explicit_preparation_status(state):
    preparer, authoring, batch, observations, _ = fixture(tools=True)
    if state == 'rejected':
        observations = (EligibilityObservation.bind(batch.requests[0], response(batch.requests[0],
            change=lambda value: value.update(status='rejected', reason_code='no_capacity'))),)
    now = NOW + timedelta(seconds=6) if state == 'expired' else NOW
    result = preparer.prepare(None, authoring, batch, observations, clock=lambda: now)
    assert result.status == ('ready_to_journal' if state == 'candidate' else 'eligibility_' + state)
    assert result.observations == observations


def test_clock_is_sampled_after_current_source_refresh():
    preparer, authoring, batch, observations, data = fixture(tools=True)
    def clock():
        assert data.calls
        return NOW + timedelta(seconds=6)
    assert preparer.prepare(None, authoring, batch, observations, clock=clock).status == 'eligibility_expired'


def test_processing_denial_preserves_original_accounting_and_proposal():
    preparer, authoring, batch, observations, data = fixture()
    original = preparer.origin.value
    data.denied.add(next(iter(data.bodies)))
    result = preparer.prepare(None, authoring, batch, observations)
    assert result.status == 'input_unavailable' and result.refresh.failures
    assert result.origin == original and result.authoring == authoring


@pytest.mark.parametrize('field', ['preparation', 'attempt', 'reservation', 'settlement'])
def test_missing_origin_or_accounting_never_becomes_prepared(field):
    preparer, authoring, batch, observations, data = fixture()
    preparer.origin.value = replace(preparer.origin.value, **{field: None})
    with pytest.raises(ValueError, match='campaign_origin_'):
        preparer.prepare(None, authoring, batch, observations)
    assert not data.calls


def test_changing_a_retained_charge_is_rejected():
    preparer, authoring, batch, observations, data = fixture()
    original = preparer.origin.value
    altered = replace(original.settlement, charge=replace(original.settlement.charge, accounting_units=1))
    preparer.origin.value = replace(original, settlement=altered)
    with pytest.raises(ValueError, match='campaign_origin_settlement'):
        preparer.prepare(None, authoring, batch, observations)
    assert not data.calls


def test_eligibility_coverage_and_foreign_check_cannot_be_substituted():
    preparer, authoring, batch, observations, data = fixture(tools=True)
    with pytest.raises(ValueError, match='compiler_preparation_coverage'):
        preparer.prepare(None, authoring, batch, ())
    other = EligibilityBatch.bind(batch.review, batch.budget, batch.configuration, 'other-check')
    with pytest.raises(ValueError, match='compiler_preparation_request'):
        preparer.prepare(None, authoring, other, observations)
    assert not data.calls and preparer.origin.calls == 0


def test_missing_science_remains_visible_in_combined_preparation():
    preparer, authoring, batch, observations, _ = fixture(research={'omitted': ('question', 'need', 'assessment')})
    result = preparer.prepare(None, authoring, batch, observations)
    assert result.status == 'ready_to_journal' and len(result.refresh.scientific_gaps) == 3


def test_relevant_tool_change_blocks_only_new_preparation():
    preparer, authoring, batch, observations, _ = fixture(tools=True)
    record = authoring.review.composition.uses[0].release.record.document()
    preparer.refresh.registry.transport.responses = [record.model_copy(update={'status': 'revoked'})]
    result = preparer.prepare(None, authoring, batch, observations, clock=lambda: NOW)
    assert result.status == 'relevant_input_changed' and result.authoring == authoring
