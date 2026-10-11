"""Retained graph selections are explicit; unavailable snapshots are never guessed."""

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_agent_planning.campaign_graph_context import CampaignGraphProjection
from amphora_agent_planning.campaign_origin.knowledge import KnowledgeOrigin
from amphora_agent_planning.campaign_proposals.observations import ObservedInput, ObservationKey

from ..campaign_graph_context.test_projection import minimal, project


@pytest.mark.parametrize('available', [True, False])
def test_exact_graph_context_and_unavailable_selection(available):
    selection, peer = minimal()
    graph = project(selection, peer) if available else CampaignGraphProjection.unavailable(selection, 'knowledge_access_denied')
    value = json.loads(graph.canonical)
    # Exercise the same retained preparation interface with real owned graph values.
    row = {'lane': 'graph', 'identity': {'selection': selection.sha256}, 'payload': value}
    prepared = SimpleNamespace(attempt=SimpleNamespace(request=selection.request), inputs=SimpleNamespace(
        preparation=SimpleNamespace(packet=SimpleNamespace(context=lambda: {'slices': [row]})),
        entries=tuple(ObservedInput(ObservationKey('graph', item.kind, item.identity), item.sha256)
                      for item in graph.observations)))
    result = KnowledgeOrigin.from_proposal(prepared)
    assert result.graph == selection.parts()[0].graph
    assert result.selection_sha256 == selection.sha256
    assert result.status == ('available' if available else 'unavailable')
    if available:
        assert result.head == selection.parts()[0].base
        assert result.assertions == selection.parts()[2]
        assert result.unavailable is None
    else:
        assert result.head is None and not result.assertions and result.context_sha256 is None
    prepared.inputs.entries = ()
    with pytest.raises(ValueError, match='origin_knowledge_observations'):
        KnowledgeOrigin.from_proposal(prepared)


@pytest.mark.parametrize('case', ['request', 'selection', 'scope'])
def test_changed_graph_origin_fails_closed(case):
    selection, peer = minimal()
    value = json.loads(project(selection, peer).canonical)
    if case == 'request':
        value['request_sha256'] = '0' * 64
    elif case == 'selection':
        value['selection_sha256'] = '0' * 64
    else:
        value['selection']['graph']['scope']['project_id'] = 'foreign'
    with pytest.raises(ValueError):
        KnowledgeOrigin.bind(selection.request, value)


@pytest.mark.parametrize('available', [True, False])
def test_full_original_preparation_to_saved_draft_keeps_graph_pins(available):
    from amphora_agent_planning.access import Principal
    from amphora_agent_planning.campaign_authoring import AuthoringPlan
    from amphora_agent_planning.campaign_decisions import CampaignDecisionReview
    from amphora_agent_planning.campaign_dispatch import CompilerEffect, CompilerObservation, CompilerSelection
    from amphora_agent_planning.campaign_eligibility import EligibilityConfiguration
    from amphora_agent_planning.campaign_knowledge_access import CampaignGraphSelection, CampaignKnowledgeReader
    from amphora_agent_planning.campaign_origin import OriginProjection
    from ..campaign_decisions.test_policy import fixture
    from ..campaign_proposals.test_evidence import prepared
    from ..campaign_authoring.test_values import saved

    proposal, declaration, budget, source = fixture(include_plan=True)
    selection, peer = minimal()
    selection = CampaignGraphSelection.bind(source.request, *selection.parts())
    result = CampaignKnowledgeReader(peer).read(selection)
    if not available:
        result = replace(result, context=None, failure='knowledge_access_denied')
    composed = prepared(source.with_graph(result), proposal.output.document().model_dump(mode='json'))
    authoring = AuthoringPlan.bind(CampaignDecisionReview.bind(composed, declaration, budget), budget,
                                  owner_id='runtime', actor_id='compiler')
    original = source.request.document()
    principal = Principal(original.actor_id, original.reference.scope, frozenset({'read_attempts', 'record_attempts'}))
    eligibility = EligibilityConfiguration.bind(owner_id='registry', actor_id='compiler', policy_sha256='e' * 64)
    selected = CompilerSelection.bind(principal, authoring, eligibility)
    effect = CompilerEffect.authoring(selected, principal, authoring, eligibility)
    outcome = saved(authoring)
    observation = CompilerObservation.bind(selected, effect, outcome.request, outcome.receipt, outcome.readback)
    projection = OriginProjection.bind(principal, selected, authoring, eligibility, observation)
    assert projection.document().origin.knowledge.status == ('available' if available else 'unavailable')
    assert projection.document().origin.knowledge.selection_sha256 == selection.sha256
