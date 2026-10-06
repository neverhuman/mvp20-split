"""Original observation bytes and concrete slot identity are independently pinned."""

import base64
import json

import pytest
from amphora_campaign_runtime.compiler.addresses import ActivationAddress
from amphora_campaign_runtime.supervision_checkpoints import CheckpointSeed
from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_campaign_runtime.supervision_scope import NodeObservation
from amphora_campaign_runtime.supervision_scope.checkpoints import (
    CheckpointFootprint,
    CheckpointTarget,
)
from amphora_contracts_campaigns import ActivationPath
from amphora_contracts_graph_runtime import GraphNodeViewV3, GraphReadCut

from ..supervision_policy.support import plan, policy


def seed(*, revision=0, run='run', nested=False, index=0):
    graph = plan(nested=nested)
    reviewed = ReviewedPolicy.bind(graph, policy(graph, nested=nested))
    path = ActivationPath.model_validate_json(json.dumps({'schema_version': '2', 'node_id': 'pack',
        'occurrences': [{'kind': 'loop', 'node_id': 'loop', 'index': index}] if nested else []}))
    view = GraphNodeViewV3(activation_id=ActivationAddress.for_plan(graph, path).key, path=path,
                          kind='artifact_materialize', status='ready', reason_code=None)
    observation = NodeObservation.capture(graph.sha256, view, state={'unicode': 'α', 'count': 1}, outputs=None)
    cut = GraphReadCut(scope=graph.document.definition.scope, run_id=run, plan_sha256=graph.sha256,
                       revision=revision, frontier_revision=revision)
    footprint = CheckpointFootprint(cut, (CheckpointTarget.materialize(observation, ('a',)),), (observation,))
    return CheckpointSeed.capture(reviewed, footprint)


def test_roundtrip_preserves_selected_state_and_stable_identity_across_global_progress():
    original = seed()
    recovered = CheckpointSeed(original.canonical, original.policy)
    assert original == recovered
    assert original.footprint().observations[0].state_json == recovered.footprint().observations[0].state_json
    later = seed(revision=4)
    assert original.sha256 != later.sha256 and original.decision_id == later.decision_id
    assert original.decision_id != seed(run='another-run').decision_id
    assert seed(nested=True, index=0).decision_id != seed(nested=True, index=1).decision_id


@pytest.mark.parametrize('change,reason', [
    ('state', 'checkpoint_seed_snapshot'), ('rule', 'checkpoint_seed_rule'),
    ('policy', 'checkpoint_seed_policy'), ('fields', 'checkpoint_seed_rule'),
])
def test_corrupted_seed_cannot_reconstruct(change, reason):
    original = seed()
    data = original.document().model_dump(mode='json')
    if change == 'state':
        data['observations'][0]['state'] = base64.b64encode(b'{}').decode('ascii')
    elif change == 'rule':
        data['checkpoint_id'] = 'other'
    elif change == 'policy':
        data['policy_sha256'] = 'f' * 64
    else:
        # Reconstruct a internally coherent footprint with a field outside the pinned policy.
        footprint = original.footprint()
        changed = CheckpointFootprint(footprint.cut,
            (CheckpointTarget.materialize(footprint.observations[0], ('unknown',)),), footprint.observations)
        with pytest.raises(ValueError, match=reason):
            CheckpointSeed.capture(original.policy, changed)
        return
    with pytest.raises(ValueError, match=reason):
        CheckpointSeed(encoded(type(original.document()).model_validate_json(json.dumps(data))), original.policy)


def test_unselected_read_and_noncanonical_bytes_reject():
    original = seed()
    footprint = original.footprint()
    path = ActivationPath(schema_version='2', node_id='finish', occurrences=())
    view = GraphNodeViewV3(activation_id=ActivationAddress.for_plan(original.policy.plan, path).key,
                          path=path, kind='finish', status='waiting', reason_code=None)
    extra = NodeObservation.capture(footprint.cut.plan_sha256, view, state={}, outputs=None)
    changed = CheckpointFootprint(footprint.cut, footprint.checkpoints, (*footprint.observations, extra))
    with pytest.raises(ValueError, match='checkpoint_seed_reads'):
        CheckpointSeed.capture(original.policy, changed)
    with pytest.raises(ValueError, match='noncanonical_checkpoint_seed'):
        CheckpointSeed(original.canonical + b' ', original.policy)
    with pytest.raises(ValueError, match='checkpoint_seed_size'):
        CheckpointSeed(b'', original.policy)
