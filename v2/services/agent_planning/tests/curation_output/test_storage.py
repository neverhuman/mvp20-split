"""Original curation capture and exact proposed graph survive SQL and compiler review."""
import base64
import hashlib
import json

import pytest
from amphora_contracts_campaign_curation import campaign_curation_draft_schema
from amphora_agent_planning.campaign_artifact_context import ArtifactContextItem, ArtifactContextPlan, ArtifactContextProjection
from amphora_agent_planning.campaign_authoring import AuthoringPlan
from amphora_agent_planning.campaign_decisions import CampaignDecisionReview
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_packet_profiles import reviewed_instructions
from amphora_agent_planning.campaign_preparations.journal import CampaignPreparationJournal
from amphora_agent_planning.campaign_proposals import PreparedCampaignProposal
from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.orchestration import PlanningRunner

from ..campaign_decisions.test_policy import fixture
from ..persistence.test_reservations import policy
from ..providers.test_task_output import Response


def selected(stored):
    previous, declaration, _budget, source = fixture(scope=stored.principal.scope, include_plan=True)
    value = source.request.document().model_dump(mode='json')
    body = reviewed_instructions('curation')
    value['context']['prompt'].update(sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body))
    value['context']['output_schema'] = campaign_curation_draft_schema().model_dump(mode='json')
    snapshot = RequestSnapshot.from_bytes(json.dumps(value).encode(), actor_id=stored.principal.actor_id,
                                         scope=stored.principal.scope)
    bodies = {row.document()['identity']['artifact_id']: base64.b64decode(row.document()['payload']['body_base64'])
              for row in source.slices}
    bodies[value['context']['prompt']['artifact_id']] = body
    artifact_plan = ArtifactContextPlan.bind(snapshot)
    items = tuple(ArtifactContextItem.available(row, bodies[row.reference.artifact_id]) for row in artifact_plan.items)
    plan = CampaignSlicePlan.from_artifacts(ArtifactContextProjection.bind(artifact_plan, items))
    return plan, declaration, previous.output.document().candidate


@pytest.mark.parametrize('kind', ['propose_campaign', 'request_capabilities'])
def test_sql_replacement_preserves_original_output_and_compiler_graph(stored, kind):
    plan, declaration, candidate = selected(stored)
    outcome = {'kind': kind, 'candidate': candidate.model_dump(mode='json'), 'gaps': []}
    if kind == 'request_capabilities':
        outcome = {'kind': kind, 'gaps': [{'gap_key': 'heat', 'purpose': 'Heat material', 'inputs': [],
            'outputs': [{'name': 'mixture', 'representation': 'mixture', 'schema_ref': None,
                         'description': 'Changed material state', 'unit': None}], 'applicability': ['synthetic'],
            'evidence_need': 'Thermal history', 'acceptance_criteria': ['Retain input identity'],
            'graph_gap': 'After combining materials'}]}
    raw = json.dumps({'schema_version': '1', 'profile': 'planning.campaign-curation-draft.v1',
        'authority': 'proposal_only', 'scientific_authority': 'not_established',
        'decision_scope': declaration.sha256, 'rationale': 'One future iteration', 'outcome': outcome,
        'unresolved': []}, indent=2).encode()
    stored.journal.register(stored.principal, plan.request)
    preparation = CampaignPreparationJournal(stored.engine).register(stored.principal, plan, prepare(plan).packet)
    provider = Response(raw)
    runner = PlanningRunner(stored.engine, provider, timeout_seconds=30)
    reviewed = policy(plan.request)
    first = runner.run(stored.principal, plan.request, reviewed)
    assert first.stop_reason == ('proposed' if kind == 'propose_campaign' else 'abstained')
    replacement_provider = Response(b'not used')
    replacement = PlanningRunner(stored.engine, replacement_provider, timeout_seconds=30)
    assert replacement.run(stored.principal, plan.request, reviewed) == first
    assert provider.calls == 1 and replacement_provider.calls == 0
    observed = first.latest.observation
    assert observed.capture.content == raw
    restored = CampaignPreparationJournal(stored.engine).read(stored.principal, plan.request.document().reference)
    assert restored == preparation
    proposal = PreparedCampaignProposal.bind(restored.record, first.latest.binding, observed)
    assert proposal.output.document().outcome.kind == kind
    assert proposal.output.proposal().payload_sha256 == observed.document().proposal.payload_sha256
    if kind == 'propose_campaign':
        review = CampaignDecisionReview.bind(proposal, declaration, reviewed)
        authoring = AuthoringPlan.bind(review, reviewed, owner_id='runtime-fixture', actor_id='planning-agent')
        assert authoring.save().payload().definition == candidate.definition
    else:
        assert proposal.review_document().candidate is None
        assert proposal.output.document().outcome.gaps[0].gap_key == 'heat'
