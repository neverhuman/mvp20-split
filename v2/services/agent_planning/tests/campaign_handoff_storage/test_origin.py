"""Actual owned SQL proves exact immutable origin, accounting and read authority."""

from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_authoring import AuthoringPlan
from amphora_agent_planning.campaign_data_access import CampaignArtifactReader
from amphora_agent_planning.campaign_decisions import CampaignDecisionReview
from amphora_agent_planning.campaign_eligibility import (
    EligibilityBatch,
    EligibilityConfiguration,
)
from amphora_agent_planning.campaign_handoff import (
    CampaignOriginReader,
    CompilerPreparer,
)
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_preparations.journal import (
    CampaignPreparationJournal,
)
from amphora_agent_planning.campaign_refresh import RefreshCollector, RefreshPlan
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.settlement import SettlementJournal
from amphora_contracts_core import Scope
from sqlalchemy import create_engine

from ..campaign_decisions.test_policy import fixture
from ..campaign_refresh.test_collection import Data
from ..persistence.test_reservations import policy

pytestmark = pytest.mark.postgres


def seeded(stored, *, omit=None, change=None):
    proposal, declaration, budget, selected = fixture(scope=stored.principal.scope, include_plan=True, change=change)
    review = CampaignDecisionReview.bind(proposal, declaration, budget)
    if omit == 'request':
        return review, budget
    stored.journal.register(stored.principal, proposal.attempt.request)
    if omit != 'preparation':
        CampaignPreparationJournal(stored.engine).register(stored.principal, selected, prepare(selected).packet)
    if omit != 'reservation':
        BudgetLedger(stored.engine).reserve(stored.principal, proposal.attempt, budget)
    else:
        stored.journal.begin_attempt(stored.principal, proposal.attempt)
    if omit != 'observation':
        stored.journal.record(stored.principal, proposal.attempt, proposal.observation)
    if omit not in {'observation', 'reservation', 'settlement'}:
        SettlementJournal(stored.engine).settle(stored.principal, proposal.attempt)
    return review, budget


def test_origin_read_and_replacement_preserve_exact_accounting(stored):
    review, budget = seeded(stored)
    reader = CampaignOriginReader(stored.engine)
    original = reader.read(stored.principal, review, budget)
    assert original.review == review and original.reservation.demand == review.demand
    assert original.settlement.charge.accounting_units == 60
    assert reader.read(stored.principal, review, budget) == original
    replacement = create_engine(stored.engine.url)
    try:
        assert CampaignOriginReader(replacement).read(stored.principal, review, budget) == original
    finally:
        replacement.dispose()


@pytest.mark.parametrize(('omit', 'error'), [('request', 'request_unknown'), ('preparation', 'campaign_origin_preparation'),
    ('reservation', 'campaign_origin_reservation'), ('observation', 'campaign_origin_observation'), ('settlement', 'campaign_origin_settlement')])
def test_incomplete_owned_history_cannot_prepare_a_handoff(stored, omit, error):
    review, budget = seeded(stored, omit=omit)
    with pytest.raises(ValueError, match=error):
        CampaignOriginReader(stored.engine).read(stored.principal, review, budget)


@pytest.mark.parametrize('denial', ['permission', 'actor', 'scope'])
def test_original_actor_scope_and_read_grant_are_required(stored, denial):
    review, budget = seeded(stored)
    principal = stored.principal
    if denial == 'permission':
        principal = replace(principal, actions=frozenset())
    elif denial == 'actor':
        principal = replace(principal, actor_id='foreign')
    else:
        principal = replace(principal, scope=Scope(tenant_id=principal.scope.tenant_id, project_id='foreign'))
    with pytest.raises((PermissionError, ValueError), match='planning_access_denied|request_actor_mismatch'):
        CampaignOriginReader(stored.engine).read(principal, review, budget)


def test_another_valid_output_cannot_replace_the_recorded_capture(stored):
    _review, budget = seeded(stored)
    changed, declaration, _ = fixture(scope=stored.principal.scope, change=lambda value: value['candidate'].update(title='Changed'))
    different = CampaignDecisionReview.bind(changed, declaration, budget)
    with pytest.raises(ValueError, match='campaign_origin_observation'):
        CampaignOriginReader(stored.engine).read(stored.principal, different, budget)


def test_new_budget_policy_cannot_reprice_original_reservation(stored):
    review, _ = seeded(stored)
    proposal = review.composition.evidence.proposal
    replacement = policy(proposal.attempt.request, units=50)
    changed = CampaignDecisionReview.bind(proposal, review.declaration, replacement)
    with pytest.raises(ValueError, match='campaign_origin_reservation'):
        CampaignOriginReader(stored.engine).read(stored.principal, changed, replacement)


def test_combined_preparation_uses_actual_stored_origin_without_accounting_writes(stored):
    review, budget = seeded(stored)
    authoring = AuthoringPlan.bind(review, budget, owner_id='runtime-fixture', actor_id='planning-agent')
    configuration = EligibilityConfiguration.bind(owner_id='registry-fixture', actor_id='planning-agent', policy_sha256='e' * 64)
    batch = EligibilityBatch.bind(review, budget, configuration, 'owned-check')
    data = Data(RefreshPlan.bind(review, budget))
    collector = RefreshCollector(artifacts=CampaignArtifactReader(data), research=None, registry=None, runtime=None)
    origin = CampaignOriginReader(stored.engine)
    before = origin.read(stored.principal, review, budget)
    result = CompilerPreparer(origin, collector).prepare(stored.principal, authoring, batch, ())
    assert result.status == 'ready_to_journal' and result.origin == before
    assert origin.read(stored.principal, review, budget) == before
    assert data.calls
