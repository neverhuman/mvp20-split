"""Original intent binding must coexist with independent compiler policy authority."""
import base64
import json

from amphora_agent_planning.curation_context import CurationIntent
from amphora_agent_planning.curation_intake.commands import CurationCommand
from amphora_agent_planning.campaign_decisions import DecisionDeclaration, CampaignDecisionReview
from amphora_agent_planning.campaign_artifact_context import ArtifactContextItem, ArtifactContextPlan, ArtifactContextProjection
from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_preparations import CampaignPreparation
from amphora_agent_planning.campaign_proposals import PreparedCampaignProposal
from amphora_agent_planning.campaign_authoring import AuthoringPlan
from amphora_agent_planning.context import RequestSnapshot, AttemptBinding
from amphora_agent_planning.providers import observe
from ..curation_output.test_storage import selected
from ..curation_intake.test_commands import request as command
from ..persistence.test_reservations import policy
from ..providers.test_task_output import Response


def test_original_intent_keeps_reviewed_declaration_and_compiles_exact_model_graph(stored):
    source, declaration, candidate = selected(stored)
    raw = command()
    raw['identity']['actor_id'] = stored.principal.actor_id
    raw['identity']['scope'] = stored.principal.scope.model_dump(mode='json')
    raw['payload']['context']['draft']['scope'] = stored.principal.scope.model_dump(mode='json')
    incoming = CurationCommand.restore(json.dumps(raw))
    request = source.request.document().model_dump(mode='json')
    request['reference']['engagement_id'] = CurationIntent.engagement_for(incoming)
    reviewed = declaration.document().model_dump(mode='json')
    reviewed['engagement'] = request['reference']
    revised = DecisionDeclaration.from_bytes(json.dumps(reviewed).encode())
    request['decision_scope'] = revised.sha256
    bodies = {row.document()['identity']['artifact_id']: base64.b64decode(row.document()['payload']['body_base64'])
              for row in source.slices}
    for entry in request['context']['entries']:
        if entry['artifact']['sha256'] == declaration.sha256:
            entry['artifact'].update(sha256=revised.sha256, size_bytes=len(revised.canonical))
            bodies[entry['artifact']['artifact_id']] = revised.canonical
    snapshot = RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id=stored.principal.actor_id,
                                          scope=stored.principal.scope)
    intent = CurationIntent.bind(snapshot, incoming)
    artifacts = ArtifactContextPlan.bind(snapshot)
    items = tuple(ArtifactContextItem.available(row, bodies[row.reference.artifact_id]) for row in artifacts.items)
    plan = CampaignSlicePlan.from_artifacts(ArtifactContextProjection.bind(artifacts, items)).with_curation(intent)
    preparation = CampaignPreparation.bind(plan, prepare(plan).packet)
    output = {'schema_version': '1', 'profile': 'planning.campaign-curation-draft.v1',
        'authority': 'proposal_only', 'scientific_authority': 'not_established',
        'decision_scope': revised.sha256, 'rationale': 'Synthetic original graph',
        'outcome': {'kind': 'propose_campaign', 'candidate': candidate.model_dump(mode='json'), 'gaps': []},
        'unresolved': []}
    attempt = AttemptBinding(snapshot, 1)
    observed = observe(attempt, Response(json.dumps(output).encode()))
    prepared = PreparedCampaignProposal.bind(preparation, attempt, observed)
    budget = policy(snapshot)
    review = CampaignDecisionReview.bind(prepared, revised, budget)
    authoring = AuthoringPlan.bind(review, budget, owner_id='runtime', actor_id='planning')
    assert authoring.save().payload().definition == candidate.definition
    assert snapshot.document().decision_scope == revised.sha256 != incoming.command.sha256
