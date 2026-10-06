"""Actual retained-plan membership and selected state, under the owning run lock."""

import json

from amphora_contracts_campaigns import ActivationPath, parse_execution_plan
from amphora_contracts_graph_runtime import GraphReadCut
from sqlalchemy import text

from ..compiler.addresses import ActivationAddress
from ..coordinator.frontier import ScopeAddress
from ..coordinator.state import ScopeState
from ..coordinator.storage import GraphStorage
from ..graph_inspection.policy import node_view
from ..lifecycle.claims import RUN
from ..supervision_scope import NodeObservation
from ..supervision_scope.observations import require


def active_scope(conn, params, plan, path):
    for depth in range(len(path.occurrences) + 1):
        address = ScopeAddress(plan.sha256, path.occurrences[:depth])
        scope = conn.execute(text('SELECT * FROM runtime.graph_scopes WHERE ' + RUN +
            ' AND scope_key=:scope'), {**params, 'scope': address.key}).mappings().one_or_none()
        require(scope is not None and scope['status'] == 'active', 'inactive_target_scope')
        require(scope['definition_path'] == list(address.definition_path) and
                scope['occurrences'] == [item.model_dump(mode='json') for item in address.occurrences],
                'stored_scope_mismatch')
        if depth:
            parent_path = ActivationPath(schema_version='2', node_id=path.occurrences[depth - 1].node_id,
                                         occurrences=path.occurrences[:depth - 1])
            require(scope['parent_activation_id'] == ActivationAddress.for_plan(plan, parent_path).key,
                    'stored_scope_parent_mismatch')
            parent = conn.execute(text('SELECT kind,status,state,scope_key FROM runtime.graph_nodes WHERE ' + RUN +
                ' AND activation_id=:activation'), {**params, 'activation': scope['parent_activation_id']}).mappings().one_or_none()
            occurrence = path.occurrences[depth - 1]
            expected = 'iterate' if occurrence.kind == 'loop' else 'scatter'
            require(parent is not None and parent['status'] == 'issued' and parent['kind'] == expected and
                    parent['scope_key'] == ScopeAddress(plan.sha256, parent_path.occurrences).key,
                    'inactive_target_parent')
            if occurrence.kind == 'loop':
                require(parent['state'].get('iteration') == occurrence.index, 'target_occurrence_mismatch')
            else:
                require(parent['state'].get('membership_sha256') == occurrence.membership_sha256 and
                        parent['state'].get('next_index', 0) > occurrence.index, 'target_occurrence_mismatch')
        else:
            require(scope['parent_activation_id'] is None, 'stored_scope_parent_mismatch')


def verify_current(conn, params, run, frame):
    require(run['status'] == 'running' and run['execution_mode'] == 'graph', 'run_not_running')
    graph = GraphStorage.graph(conn, params)
    document = conn.execute(text('SELECT document FROM runtime.graph_plans WHERE tenant_id=:tenant '
        'AND project_id=:project AND plan_sha256=:plan'), {**params, 'plan': graph['plan_sha256']}).scalar_one()
    plan = parse_execution_plan(json.dumps(document))
    require(plan.sha256 == graph['plan_sha256'], 'stored_plan_mismatch')
    original = frame.footprint()
    rows = conn.execute(text('SELECT * FROM runtime.graph_nodes WHERE ' + RUN +
        ' AND activation_id=ANY(:ids)'), {**params, 'ids': [item.identity for item in original.observations]}).mappings().all()
    observations = []
    for row in rows:
        view = node_view(row)
        address = ActivationAddress.for_plan(plan, view.path)
        require(address.key == row['activation_id'] and row['node_id'] == view.path.node_id,
                'stored_node_identity_mismatch')
        body = plan.document.definition.body
        for occurrence in view.path.occurrences:
            body = next(item.body for item in body.nodes if item.node_id == occurrence.node_id)
        definition = next(item for item in body.nodes if item.node_id == view.path.node_id)
        require(definition.kind == view.kind and
                row['scope_key'] == ScopeAddress(plan.sha256, view.path.occurrences).key, 'stored_node_kind_mismatch')
        if row['activation_id'] in original.targets:
            active_scope(conn, params, plan, view.path)
            materialized = conn.execute(text('SELECT 1 FROM runtime.activations WHERE ' + RUN +
                ' AND activation_id=:activation'), {**params, 'activation': row['activation_id']}).first()
            require(materialized is None, 'target_already_materialized')
            if frame.request.schema_version == '2':
                target = next(item for item in original.checkpoints if item.activation_id == row['activation_id'])
                if target.kind == 'artifact_materialize':
                    opened = conn.execute(text('SELECT 1 FROM runtime.binding_intents WHERE ' + RUN +
                        ' AND activation_id=:activation'), {**params, 'activation': row['activation_id']}).first()
                    require(opened is None, 'target_conversion_already_opened')
                    fields = {item.name: item for item in definition.fields}
                    require(set(target.fields) <= fields.keys(), 'checkpoint_field_missing')
                    state = ScopeState.load(conn, params, plan, row['scope_key'])
                    for name in target.fields:
                        require(fields[name].mode == 'inline', 'checkpoint_field_not_inline')
                        value = state.environment.source(fields[name].source)
                        require(value.kind in {'boolean', 'integer', 'number', 'string'}, 'checkpoint_field_not_scalar')
        observations.append(NodeObservation.capture(plan.sha256, view, state=row['state'], outputs=row['outputs']))
    cut = GraphReadCut(scope=frame.request.reference.scope, run_id=params['run'], plan_sha256=plan.sha256,
                       revision=run['revision'], frontier_revision=graph['frontier_revision'])
    require(not original.compare(cut, tuple(observations)).stale, 'selected_observation_changed')
    deadline = frame.request.deadline_unix_ms
    valid = conn.execute(text('SELECT clock_timestamp() < to_timestamp(:deadline / 1000.0) '
        'AND to_timestamp(:deadline / 1000.0) <= :graph_deadline'),
        {'deadline': deadline, 'graph_deadline': graph['deadline']}).scalar_one()
    require(valid, 'supervision_deadline_unavailable')
