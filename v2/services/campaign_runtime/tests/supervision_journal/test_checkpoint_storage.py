"""Real Runtime journal retains explicit conversion targets before any publication."""

import copy
import hashlib
import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.compiler import ToolCatalog
from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.graph_inspection.policy import node_view
from amphora_campaign_runtime.supervision_journal.cancellations import (
    CancellationJournal,
)
from amphora_campaign_runtime.supervision_journal.checkpoint_frames import (
    CheckpointFrame,
    read_frame,
)
from amphora_campaign_runtime.supervision_journal.delivery import DeliveryJournal
from amphora_campaign_runtime.supervision_journal.responses import ResponseJournal
from amphora_campaign_runtime.supervision_journal.storage import (
    RequestJournal,
    outgoing,
)
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_campaign_runtime.supervision_requests.projection import CheckpointExport
from amphora_campaign_runtime.supervision_scope import NodeObservation
from amphora_campaign_runtime.supervision_scope.checkpoints import (
    CheckpointFootprint,
    CheckpointTarget,
)
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_graph_runtime import GraphReadCut
from amphora_contracts_supervision import (
    CheckpointRequest,
    SupervisionCommandReceipt,
    parse_checkpoint_command,
)
from sqlalchemy import text

from ..compiler.test_bindings import CASES, output_schema
from .test_cancellations import incoming as cancellation_command
from .test_checkpoint_frames import frame as literal_frame
from .test_responses import incoming as response_command
from .test_storage import setup as invoke_setup


def setup(g, fields=('a',)):
    e = g.env
    e.principal = replace(e.principal, actions=e.principal.actions | {'supervise_prepare', 'supervise_dispatch'})
    raw = copy.deepcopy(CASES[4]['payload'])
    raw['scope'] = e.principal.scope.model_dump(mode='json')
    raw['body']['nodes'][0]['fields'].append({'name': 'a', 'mode': 'inline',
        'source': {'kind': 'integer', 'value': 1, 'unit': '1'}})
    schemas = output_schema(raw, {'type': 'object', 'properties': {'a': {'type': 'integer'},
        'values': {'type': 'array', 'items': {'type': 'number'}, 'maxItems': 3}}, 'required': ['a', 'values']})
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), schemas)
    reply = GraphAdmission(e.engine, PlanCatalog([entry]), bindings_enabled=True).admit(e.principal,
        g.command('graph.admit', {'plan_sha256': entry.plan.sha256, 'inputs': [
            {'port': 'parameters', 'value': {'kind': 'collection', 'items': []}}], 'budget': {'limit': 1}}))
    assert reply.outcome.status == 'accepted'
    run = reply.outcome.committed.object_id
    params = RequestJournal.params(e.principal, run, 'checkpoint-decision')
    with e.engine.connect() as conn:
        graph = conn.execute(text('SELECT r.revision,g.plan_sha256,g.frontier_revision,'
            'floor(extract(epoch from g.deadline)*1000)::bigint AS deadline FROM runtime.runs r '
            'JOIN runtime.graph_runs g USING(tenant_id,project_id,run_id) WHERE '
            'r.tenant_id=:tenant AND r.project_id=:project AND r.run_id=:run'), params).mappings().one()
        row = conn.execute(text("SELECT * FROM runtime.graph_nodes WHERE tenant_id=:tenant AND project_id=:project "
            "AND run_id=:run AND kind='artifact_materialize'"), params).mappings().one()
    cut = GraphReadCut(scope=e.principal.scope, run_id=run, plan_sha256=entry.plan.sha256,
        revision=graph['revision'], frontier_revision=graph['frontier_revision'])
    observation = NodeObservation.capture(entry.plan.sha256, node_view(row), state=row['state'], outputs=row['outputs'])
    footprint = CheckpointFootprint(cut, (CheckpointTarget.materialize(observation, fields),), (observation,))
    data = literal_frame().request.model_dump(mode='json')
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}:
                value.update(e.principal.scope.model_dump(mode='json'))
            else:
                for item in value.values():
                    rescope(item)
        elif isinstance(value, list):
            for item in value:
                rescope(item)
    rescope(data)
    data['reference'].update(run_id=run, decision_id='checkpoint-decision')
    data['snapshot'] = CheckpointExport(footprint).document().model_dump(mode='json')
    data['planning_request']['runtime_cut'] = cut.model_dump(mode='json')
    data['deadline_unix_ms'] = graph['deadline']
    request = CheckpointRequest.model_validate_json(json.dumps(data))
    request = request.model_copy(update={'planning_request_sha256': hashlib.sha256(encoded(request.planning_request)).hexdigest()})
    frame = CheckpointFrame.capture(request, footprint, prepared_by=e.principal.actor_id, planning_actor='fixture')
    journal = RequestJournal(e.engine, {(e.principal.scope.tenant_id, e.principal.scope.project_id,
                                       e.principal.actor_id): 'fixture'})
    return journal, frame


def command(frame):
    return parse_checkpoint_command(json.dumps({'encoding': 'amphora-command-v2', 'identity': {
        'scope': frame.request.reference.scope.model_dump(mode='json'), 'actor_id': 'fixture',
        'command_family': 'planning.supervision.request.v2', 'command_id': 'checkpoint-request'},
        'payload': frame.request.model_dump(mode='json')}))


def test_v2_prepare_delivery_readback_and_replacement(graph_env):
    journal, frame = setup(graph_env)
    principal = graph_env.env.principal
    incoming = command(frame)
    first = journal.prepare(principal, frame, incoming.canonical_bytes)
    assert first.frame.canonical == frame.canonical and read_frame(frame.canonical) == frame
    replacement = RequestJournal(graph_env.env.engine, journal.planning_actors)
    assert replacement.prepare(principal, frame, incoming.canonical_bytes) == first
    stored = replacement.series(principal, frame.request.reference.run_id, frame.request.reference.decision_id)
    assert stored == (first,) and outgoing(frame, first.canonical_command) == incoming
    delivery = DeliveryJournal(replacement)
    lease = delivery.claim(principal, frame.request.reference, frame.request_sha256, event_id='claim')
    receipt = SupervisionCommandReceipt.model_validate({'outcome': {'status': 'recorded', 'binding': {
        'identity': incoming.identity, 'request_sha256': incoming.sha256, 'operation_id': 'fixture-record'},
        'committed': {'kind': 'request', 'object_id': frame.request.planning_request.reference.engagement_id,
                      'revision': 1, 'content_sha256': frame.request_sha256}}})
    event = delivery.observe(principal, lease, event_id='observed', receipt=receipt, readback=frame.request)
    assert event.kind == 'recorded' and event.evidence.profile == 'runtime-supervision-delivery.v2'
    assert DeliveryJournal(replacement).history(principal, frame.request.reference, frame.request_sha256)[-1] == event


@pytest.mark.parametrize('fields,reason', [(('absent',), 'checkpoint_field_missing'),
                                         (('values',), 'checkpoint_field_not_scalar')])
def test_actual_plan_field_authority_rejects_before_storage(graph_env, fields, reason):
    journal, frame = setup(graph_env, fields)
    with pytest.raises(ValueError, match=reason):
        journal.prepare(graph_env.env.principal, frame, command(frame).canonical_bytes)
    assert journal.series(graph_env.env.principal, frame.request.reference.run_id, frame.request.reference.decision_id) == ()


def test_opened_binding_cannot_acquire_new_checkpoint(graph_env):
    journal, frame = setup(graph_env)
    class NoPublication:
        def tick(self, principal):
            pass
    GraphAdvancer(graph_env.env.engine, bindings=NoPublication()).advance(graph_env.env.principal,
        graph_env.command('graph.advance', {'run_id': frame.request.reference.run_id, 'max_transitions': 1}))
    with pytest.raises(ValueError, match='target_conversion_already_opened'):
        journal.prepare(graph_env.env.principal, frame, command(frame).canonical_bytes)


def test_response_and_cancellation_recover_against_original_v2_frame(graph_env):
    journal, frame = setup(graph_env)
    journal.prepare(graph_env.env.principal, frame, command(frame).canonical_bytes)
    actor = replace(graph_env.env.principal, actor_id='fixture',
                    actions=frozenset({'read', 'supervise_respond', 'supervise_cancel'}))
    response, capture = response_command(frame, name='abstain')
    responses = ResponseJournal(journal)
    first = responses.record(actor, response, capture_bytes=capture)
    saved = responses.response(actor, 'response-1')
    assert saved.capture_bytes == capture and first.outcome.status == 'recorded'
    assert ResponseJournal(journal).record(actor, response, capture_bytes=capture) == first
    assert ResponseJournal(journal).response(actor, 'response-1') == saved
    cancel = cancellation_command(frame, actor.actor_id)
    cancellations = CancellationJournal(journal)
    recorded = cancellations.record(actor, cancel)
    assert recorded.outcome.status == 'recorded'
    assert CancellationJournal(journal).record(actor, cancel) == recorded
    assert CancellationJournal(journal).cancellation(actor, 'cancel-1') == cancellations.cancellation(actor, 'cancel-1')


def test_v2_invoke_review_keeps_existing_worker_input_boundary(graph_env):
    e, journal, old, _ = invoke_setup(graph_env)
    original = old.footprint()
    targets = tuple(CheckpointTarget.review(item) for item in original.observations if item.identity in original.targets)
    footprint = CheckpointFootprint(original.cut, targets, original.observations)
    request = CheckpointRequest.model_validate({**old.request.model_dump(), 'schema_version': '2',
                                               'snapshot': CheckpointExport(footprint).document()})
    frame = CheckpointFrame.capture(request, footprint, prepared_by=e.principal.actor_id, planning_actor='fixture')
    saved = journal.prepare(e.principal, frame, command(frame).canonical_bytes)
    assert saved.frame.footprint().checkpoints == targets
