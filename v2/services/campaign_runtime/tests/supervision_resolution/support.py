"""Actual admitted recipe/reservations with literal synthetic public responses."""

import hashlib
import json
from dataclasses import replace

from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.supervision_context.preparation import ContextPreparer
from amphora_campaign_runtime.supervision_journal.responses import ResponseJournal
from amphora_campaign_runtime.supervision_outcomes.reports import ReportJournal
from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.catalog import PolicyCatalog
from amphora_campaign_runtime.supervision_policy.records import RecipePolicyRecord
from amphora_campaign_runtime.supervision_preparation.catalog import RecipeCatalog
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_campaign_runtime.supervision_resolution import OutcomeResolver
from amphora_contracts_planning import CheckpointDraft, checkpoint_draft_schema
from amphora_contracts_supervision import (
    SupervisionRef,
    SupervisionResponse,
    parse_supervision_command,
)

from ..supervision_checkpoints.test_coordinator import slots
from ..supervision_context.test_preparation import Publications
from ..supervision_effects.test_proposal import proposal
from ..supervision_outcomes.test_reported import bind, report
from ..supervision_policy.support import plan, policy
from ..supervision_policy.test_admission import command
from ..supervision_preparation.test_policy_pins import configuration
from ..supervision_responses.support import response


def setup(graph, *, calls=2, prepare=True):
    actor = replace(graph.env.principal, actions=graph.env.principal.actions |
        {'supervise_prepare', 'supervise_accept', 'supervise_dispatch'})
    graph.env.principal = actor
    recipe, _ = configuration(graph)
    compiled = plan(scope=actor.scope.model_dump(mode='json'))
    graph.entry = ReviewedPlan(compiled, ())
    graph.payload = {'plan_sha256': compiled.sha256, 'inputs': [], 'budget': {'limit': 2}}
    data = policy(compiled).model_dump(mode='json')
    data.update(profile='runtime-supervision-policy.v2', context_recipe_sha256=recipe.sha256)
    data['checkpoints'][0].update(max_model_calls=calls, timeout_seconds=300)
    reviewed = ReviewedPolicy.bind(compiled, RecipePolicyRecord.model_validate_json(json.dumps(data)))
    admission = GraphAdmission(graph.env.engine, PlanCatalog([graph.entry]), bindings_enabled=True,
        policies=PolicyCatalog([reviewed]), recipes=RecipeCatalog([recipe]))
    run = admission.admit_supervised(actor, command(graph, reviewed)).outcome.committed.object_id
    slot = slots(graph, run, reviewed)[0]
    ref = SupervisionRef(scope=actor.scope, run_id=run, decision_id=slot.seed.decision_id)
    artifacts = Publications(graph, ref)
    preparer = ContextPreparer(graph.env.engine,
        {(actor.scope.tenant_id, actor.scope.project_id, actor.actor_id): 'fixture'}, artifacts)
    original = preparer.prepare(actor, ref) if prepare else None
    reports = ReportJournal(preparer.journal)
    return actor, ref, slot, preparer, original, OutcomeResolver(reports)


def record_response(actor, ref, slot, preparer, original, *, variant='valid', response_id='fixture-response', record=True):
    draft = proposal(slot.seed)
    draft['decision_scope'] = original.frame.request.planning_request.decision_scope
    if variant == 'outside':
        draft['candidate']['changes'][0]['proposed']['value'] = 11
    draft = CheckpointDraft.model_validate_json(json.dumps(draft))
    failed = variant in {'invalid', 'profile'}
    raw = b'malformed' if failed else encoded(draft)
    old, _ = response('adjustment')
    data = old.model_dump(mode='json')
    data.update(response_id=response_id, reference=ref.model_dump(mode='json'), request_sha256=original.frame.request_sha256)
    data['capture'].update(scope=actor.scope.model_dump(mode='json'), sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
    observation = data['observation']
    observation['attempt'].update(engagement=original.frame.request.planning_request.reference.model_dump(mode='json'),
        request_sha256=original.frame.request.planning_request_sha256, ordinal=1)
    observation.update(output_sha256=hashlib.sha256(raw).hexdigest(), captured_bytes=len(raw),
        status='policy_rejected' if variant == 'profile' else 'invalid' if failed else 'proposed',
        reason_code='provider_or_profile_mismatch' if variant == 'profile' else 'invalid_json' if failed else None)
    if failed:
        observation['proposal'] = None
    else:
        observation['proposal'].update(output_schema=checkpoint_draft_schema().model_dump(mode='json'),
            payload_json=raw.decode(), payload_sha256=hashlib.sha256(raw).hexdigest(), action=draft.action, rationale=draft.rationale)
    value = SupervisionResponse.model_validate_json(json.dumps(data))
    incoming = parse_supervision_command('runtime.supervision.respond', json.dumps({'encoding': 'amphora-command-v2',
        'identity': {'scope': actor.scope.model_dump(mode='json'), 'actor_id': 'fixture',
            'command_family': 'runtime.supervision.respond', 'command_id': response_id}, 'payload': value.model_dump(mode='json')}))
    responder = replace(actor, actor_id='fixture', actions=frozenset({'read', 'supervise_respond'}))
    if record:
        ResponseJournal(preparer.journal).record(responder, incoming, capture_bytes=raw)
    return value


def save_report(resolver, actor, original, response=None, *, reason='provider_unconfigured'):
    request = original.frame.request
    data = report(request, reason=reason)
    if response is not None:
        status = response.observation.status
        data['stop_reason'] = 'attempt_limit' if status == 'invalid' else status
        data['attempts'] = [{'attempt': response.observation.attempt.model_dump(mode='json'), 'status': status,
            'observation_sha256': hashlib.sha256(encoded(response.observation)).hexdigest()}]
    value = bind(data, request)
    return resolver.reports.record(actor, request.reference, original.frame.request_sha256, value)
