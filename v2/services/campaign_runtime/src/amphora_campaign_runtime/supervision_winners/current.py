"""Actual selected facts and scalar values, reconstructed under the run lock."""

from amphora_contracts_graph_runtime import GraphBinding, GraphReadCut
from sqlalchemy import text

from ..coordinator.state import ScopeState
from ..coordinator.storage import GraphStorage
from ..graph_inspection.policy import node_view
from ..lifecycle.claims import RUN
from ..supervision_checkpoints.values import ValueCheckpointSeed
from ..supervision_journal.current import verify_footprint
from ..supervision_scope import NodeObservation
from ..supervision_scope.checkpoints import CheckpointFootprint
from ..supervision_scope.observations import require


def current_seed(conn, params, run, slot):
    seed, policy = slot.seed, slot.seed.policy
    original = seed.footprint()
    rows = conn.execute(text('SELECT * FROM runtime.graph_nodes WHERE ' + RUN + ' AND activation_id=ANY(:ids)'),
        {**params, 'ids': [item.identity for item in original.observations]}).mappings().all()
    target = next((row for row in rows if row['activation_id'] == original.targets[0]), None)
    require(target is not None and target['status'] == 'ready', 'winner_target_not_ready')
    graph = GraphStorage.graph(conn, params)
    cut = GraphReadCut(scope=original.cut.scope, run_id=original.cut.run_id, plan_sha256=policy.plan.sha256,
        revision=run['revision'], frontier_revision=graph['frontier_revision'])
    observations = tuple(NodeObservation.capture(policy.plan.sha256, node_view(row),
        state=row['state'], outputs=row['outputs']) for row in rows)
    footprint = CheckpointFootprint(cut, original.checkpoints, observations)
    verify_footprint(conn, params, run, footprint)
    fields = ()
    if target['kind'] == 'artifact_materialize':
        scope = ScopeState.load(conn, params, policy.plan, target['scope_key'])
        node = scope.definition(target)
        rule = policy.rule_for(node_view(target).path)
        sources = {field.name: field.source for field in node.fields}
        fields = tuple(GraphBinding(port=field.name, value=scope.environment.source(sources[field.name]))
                       for field in rule.fields)
    result = ValueCheckpointSeed.capture(policy, footprint, fields)
    require(result.decision_id == seed.decision_id, 'winner_current_slot_mismatch')
    return result
