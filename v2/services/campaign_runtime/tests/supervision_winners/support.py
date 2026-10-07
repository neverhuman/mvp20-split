"""Admitted synthetic scalar checkpoints and exact captured owner responses."""

import hashlib
import json
from dataclasses import replace

from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.supervision_journal.checkpoint_frames import (
    CheckpointFrame,
)
from amphora_campaign_runtime.supervision_journal.responses import ResponseJournal
from amphora_campaign_runtime.supervision_journal.storage import RequestJournal
from amphora_campaign_runtime.supervision_policy import PolicyRecord, ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.catalog import PolicyCatalog
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_campaign_runtime.supervision_requests.projection import CheckpointExport
from amphora_campaign_runtime.supervision_winners import WinnerStore
from amphora_contracts_planning import CheckpointDraft, CheckpointFollowupDraft, checkpoint_draft_schema, checkpoint_followup_draft_schema
from amphora_contracts_supervision import (
    CheckpointRequest,
    SupervisionRef,
    SupervisionResponse,
    parse_supervision_command,
)

from ..supervision_checkpoints.test_coordinator import slots
from ..supervision_effects.test_proposal import proposal
from ..supervision_journal.test_checkpoint_frames import frame as literal_frame
from ..supervision_journal.test_checkpoint_storage import command as request_command
from ..supervision_policy.support import plan, policy
from ..supervision_policy.test_admission import command
from ..supervision_policy.test_admission import reviewed as invoke_policy
from ..supervision_responses.support import response


def setup(graph, *, timeout=300, fallback='continue_unchanged', invoke=False):
    actor = replace(graph.env.principal, actions=graph.env.principal.actions | {'supervise_accept', 'supervise_prepare'})
    graph.env.principal = actor
    compiled = graph.entry.plan if invoke else plan(scope=actor.scope.model_dump(mode='json'))
    if not invoke:
        graph.entry = ReviewedPlan(compiled, ())
        graph.payload = {'plan_sha256': compiled.sha256, 'inputs': [], 'budget': {'limit': 2}}
    raw = (invoke_policy(graph).document() if invoke else policy(compiled)).model_dump(mode='json')
    raw['checkpoints'][0].update(timeout_seconds=timeout, fallback=fallback)
    reviewed = ReviewedPolicy.bind(compiled, PolicyRecord.model_validate_json(json.dumps(raw)))
    admission = GraphAdmission(graph.env.engine, PlanCatalog([graph.entry]), bindings_enabled=True,
                               policies=PolicyCatalog([reviewed]))
    receipt = admission.admit_supervised(actor, command(graph, reviewed))
    run = receipt.outcome.committed.object_id
    slot = slots(graph, run, reviewed)[0]
    reference = SupervisionRef(scope=actor.scope, run_id=run, decision_id=slot.seed.decision_id)
    return WinnerStore(graph.env.engine), actor, reference, slot


def prepare(graph, actor, reference, slot, *, mutation=None, request_mutation=None, followup=False):
    data = literal_frame().request.model_dump(mode='json')
    def rescope(item):
        if isinstance(item, dict):
            if set(item) == {'tenant_id', 'project_id'}:
                item.update(actor.scope.model_dump(mode='json'))
            for value in item.values():
                rescope(value)
        elif isinstance(item, list):
            for value in item:
                rescope(value)
    rescope(data)
    data.update(reference=reference.model_dump(mode='json'), checkpoint_id=slot.seed.document().checkpoint_id,
        snapshot=CheckpointExport(slot.seed.footprint()).document().model_dump(mode='json'),
        deadline_unix_ms=int(slot.deadline.timestamp() * 1000))
    data['planning_request']['runtime_cut'] = slot.seed.footprint().cut.model_dump(mode='json')
    profile = checkpoint_followup_draft_schema() if followup else checkpoint_draft_schema()
    data['planning_request']['context']['output_schema'] = profile.model_dump(mode='json')
    data['policy']['sha256'] = slot.seed.policy.sha256
    data['planning_request']['context']['policy'] = data['policy']
    if request_mutation is not None:
        request_mutation(data)
    value = CheckpointRequest.model_validate_json(json.dumps(data))
    data['planning_request_sha256'] = hashlib.sha256(encoded(value.planning_request)).hexdigest()
    value = CheckpointRequest.model_validate_json(json.dumps(data))
    frame = CheckpointFrame.capture(value, slot.seed.footprint(), prepared_by=actor.actor_id, planning_actor='fixture')
    requests = RequestJournal(graph.env.engine, {(actor.scope.tenant_id, actor.scope.project_id, actor.actor_id): 'fixture'})
    requests.prepare(actor, frame, request_command(frame).canonical_bytes)
    draft = proposal(slot.seed)
    draft['decision_scope'] = value.planning_request.decision_scope
    if mutation is not None:
        mutation(draft)
    draft = (CheckpointFollowupDraft if followup else CheckpointDraft).model_validate_json(json.dumps(draft))
    raw = encoded(draft)
    old, _ = response('adjustment')
    data = old.model_dump(mode='json')
    data.update(reference=reference.model_dump(mode='json'), request_sha256=frame.request_sha256)
    data['capture'].update(scope=actor.scope.model_dump(mode='json'), sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
    observation = data['observation']
    observation['attempt'].update(engagement=value.planning_request.reference.model_dump(mode='json'),
                                  request_sha256=value.planning_request_sha256)
    observation.update(output_sha256=hashlib.sha256(raw).hexdigest(), captured_bytes=len(raw),
                       status='abstained' if draft.action == 'abstain' else 'proposed')
    observation['proposal'].update(output_schema=profile.model_dump(mode='json'),
        payload_json=raw.decode(), payload_sha256=hashlib.sha256(raw).hexdigest(), action=draft.action, rationale=draft.rationale)
    record = SupervisionResponse.model_validate_json(json.dumps(data))
    incoming = parse_supervision_command('runtime.supervision.respond', json.dumps({
        'encoding': 'amphora-command-v2', 'identity': {'scope': actor.scope.model_dump(mode='json'),
            'actor_id': 'fixture', 'command_family': 'runtime.supervision.respond', 'command_id': 'model-response'},
        'payload': record.model_dump(mode='json')}))
    responses = ResponseJournal(requests)
    responder = replace(actor, actor_id='fixture', actions=frozenset({'read', 'supervise_respond'}))
    responses.record(responder, incoming, capture_bytes=raw)
    return record.response_id
