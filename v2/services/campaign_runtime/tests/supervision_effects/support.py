"""Typed single-field materialization examples with independent numeric bounds."""

import hashlib
import json

from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
    compile_campaign,
)
from amphora_campaign_runtime.compiler.addresses import ActivationAddress
from amphora_campaign_runtime.supervision_checkpoints.values import ValueCheckpointSeed
from amphora_campaign_runtime.supervision_policy import PolicyRecord, ReviewedPolicy
from amphora_campaign_runtime.supervision_scope import NodeObservation
from amphora_campaign_runtime.supervision_scope.checkpoints import (
    CheckpointFootprint,
    CheckpointTarget,
)
from amphora_contracts_campaigns import ActivationPath, parse_executable_campaign
from amphora_contracts_core import SchemaRef
from amphora_contracts_graph_runtime import GraphNodeViewV3, GraphReadCut

from ..supervision_checkpoints.test_values import binding
from ..supervision_policy.support import plan, policy


def typed_seed(kind, initial, allowed):
    schema = json.dumps({'type': 'object', 'properties': {'a': {'type': kind}}, 'required': ['a'],
                         'additionalProperties': False}, sort_keys=True, separators=(',', ':')).encode()
    reference = SchemaRef(schema_id='fixture.typed-selection', version='1', sha256=hashlib.sha256(schema).hexdigest())
    data = plan().document.definition.model_dump(mode='json')
    node = next(item for item in data['body']['nodes'] if item['node_id'] == 'pack')
    node['fields'][0]['source'] = {'kind': kind, 'value': float(initial) if kind == 'number' else initial}
    node['output']['value_type']['schema_ref'] = reference.model_dump(mode='json')
    data['body']['outputs'][0]['value_type']['schema_ref'] = reference.model_dump(mode='json')
    graph = compile_campaign(parse_executable_campaign(json.dumps(data)), ToolCatalog([]),
                             SchemaCatalog([PinnedSchema(SchemaIdentity.from_wire(reference), schema)]))
    record = policy(graph).model_dump(mode='json')
    field = record['checkpoints'][0]['fields'][0]
    field['value_type']['scalar'] = kind
    field['constraint'] = ({'kind': 'range', 'minimum': {'kind': 'number', 'value': allowed[0]},
                            'maximum': {'kind': 'number', 'value': allowed[1]}} if kind == 'number' else
                           {'kind': 'choices', 'values': [{'kind': kind, 'value': value} for value in allowed]})
    reviewed = ReviewedPolicy.bind(graph, PolicyRecord.model_validate_json(json.dumps(record)))
    path = ActivationPath(schema_version='2', node_id='pack', occurrences=())
    view = GraphNodeViewV3(activation_id=ActivationAddress.for_plan(graph, path).key, path=path,
                          kind='artifact_materialize', status='ready', reason_code=None)
    observation = NodeObservation.capture(graph.sha256, view, state={}, outputs=None)
    cut = GraphReadCut(scope=graph.document.definition.scope, run_id='typed-selection', plan_sha256=graph.sha256,
                       revision=0, frontier_revision=0)
    footprint = CheckpointFootprint(cut, (CheckpointTarget.materialize(observation, ('a',)),), (observation,))
    return ValueCheckpointSeed.capture(reviewed, footprint, (binding(initial, kind=kind),))
