"""Independent installed-owner fixture: explicit scalar conversion, no peer imports."""

import hashlib
import json
from pathlib import Path

from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
)
from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.graph_inspection.policy import node_view
from amphora_campaign_runtime.supervision_journal.checkpoint_frames import (
    CheckpointFrame,
)
from amphora_campaign_runtime.supervision_journal.storage import RequestJournal
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_campaign_runtime.supervision_requests.projection import CheckpointExport
from amphora_campaign_runtime.supervision_scope import NodeObservation
from amphora_campaign_runtime.supervision_scope.checkpoints import (
    CheckpointFootprint,
    CheckpointTarget,
)
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import SchemaRef
from amphora_contracts_graph_runtime import GraphReadCut
from amphora_contracts_supervision import CheckpointRequest, parse_checkpoint_command
from sqlalchemy import text


def setup(g):
    e = g.env
    scope = e.principal.scope.model_dump(mode='json')
    schema = b'{"additionalProperties":false,"properties":{"a":{"type":"integer"}},"required":["a"],"type":"object"}'
    reference = SchemaRef(schema_id='fixture.checkpoint-parameters', version='1', sha256=hashlib.sha256(schema).hexdigest())
    shape = {'kind': 'artifact', 'schema_ref': reference.model_dump(mode='json'),
             'representation': 'fixture.parameters', 'unit': '1', 'media_type': 'application/json'}
    output = {'name': 'result', 'value_type': shape}
    raw = {**g.raw, 'schema_version': '4', 'profile': 'deterministic-v3', 'scope': scope,
        'body': {'inputs': [], 'outputs': [output], 'nodes': [
            {'kind': 'artifact_materialize', 'node_id': 'parameters', 'fields': [
                {'name': 'a', 'mode': 'inline', 'source': {'kind': 'integer', 'value': 1, 'unit': '1'}}],
                'output': output},
            {'kind': 'finish', 'node_id': 'finish', 'outputs': [
                {'port': 'result', 'source': {'kind': 'output', 'node_id': 'parameters', 'port': 'result'}}]}],
            'edges': [{'source': 'parameters', 'target': 'finish', 'route': 'next'}]}}
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]),
        SchemaCatalog([PinnedSchema(SchemaIdentity.from_wire(reference), schema)]))
    reply = GraphAdmission(e.engine, PlanCatalog([entry]), bindings_enabled=True).admit(e.principal,
        g.command('graph.admit', {'plan_sha256': entry.plan.sha256, 'inputs': [], 'budget': {'limit': 1}}))
    assert reply.outcome.status == 'accepted'
    params = RequestJournal.params(e.principal, reply.outcome.committed.object_id, 'checkpoint-decision')
    with e.engine.connect() as conn:
        graph = conn.execute(text('SELECT r.revision,g.frontier_revision,'
            'floor(extract(epoch from g.deadline)*1000)::bigint AS deadline FROM runtime.runs r '
            'JOIN runtime.graph_runs g USING(tenant_id,project_id,run_id) '
            'WHERE r.tenant_id=:tenant AND r.project_id=:project AND r.run_id=:run'), params).mappings().one()
        row = conn.execute(text("SELECT * FROM runtime.graph_nodes WHERE tenant_id=:tenant AND project_id=:project "
            "AND run_id=:run AND kind='artifact_materialize'"), params).mappings().one()
    cut = GraphReadCut(scope=e.principal.scope, run_id=params['run'], plan_sha256=entry.plan.sha256,
                       revision=graph['revision'], frontier_revision=graph['frontier_revision'])
    observation = NodeObservation.capture(entry.plan.sha256, node_view(row), state=row['state'], outputs=row['outputs'])
    footprint = CheckpointFootprint(cut, (CheckpointTarget.materialize(observation, ('a',)),), (observation,))
    fixture = Path(__file__).parents[1] / 'supervision_journal/fixtures/checkpoint-frame.json'
    data = CheckpointFrame.from_bytes(fixture.read_bytes()).request.model_dump(mode='json')
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}:
                value.update(scope)
            else:
                for item in value.values():
                    rescope(item)
        elif isinstance(value, list):
            for item in value:
                rescope(item)
    rescope(data)
    data['reference'].update(run_id=params['run'], decision_id=params['decision'])
    data['snapshot'] = CheckpointExport(footprint).document().model_dump(mode='json')
    data['planning_request']['runtime_cut'] = cut.model_dump(mode='json')
    data['deadline_unix_ms'] = graph['deadline']
    request = CheckpointRequest.model_validate_json(json.dumps(data))
    request = request.model_copy(update={'planning_request_sha256': hashlib.sha256(encoded(request.planning_request)).hexdigest()})
    frame = CheckpointFrame.capture(request, footprint, prepared_by=e.principal.actor_id, planning_actor='fixture')
    journal = RequestJournal(e.engine, {(params['tenant'], params['project'], e.principal.actor_id): 'fixture'})
    return e, journal, frame, params


def command(frame):
    return parse_checkpoint_command(json.dumps({'encoding': 'amphora-command-v2', 'identity': {
        'scope': frame.request.reference.scope.model_dump(mode='json'), 'actor_id': 'fixture',
        'command_family': 'planning.supervision.request.v2', 'command_id': 'checkpoint-request'},
        'payload': frame.request.model_dump(mode='json')})).canonical_bytes
