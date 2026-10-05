"""Owned projection and original Planning byte-binding compatibility."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_campaign_runtime.compiler.addresses import ActivationAddress
from amphora_campaign_runtime.supervision_requests import (
    ScopeExport,
    SupervisionRequestBinding,
)
from amphora_campaign_runtime.supervision_scope import (
    DecisionFootprint,
    NodeObservation,
)
from amphora_contracts_campaigns import ActivationPath
from amphora_contracts_graph_runtime import GraphNodeViewV3
from amphora_contracts_supervision import SupervisionRequest

FIXTURES = Path(__file__).absolute().parents[4] / 'contracts/supervision/tests/fixtures'


def original():
    return SupervisionRequest.model_validate_json((FIXTURES / 'request.json').read_bytes())


def footprint():
    request = original()
    observations = tuple(NodeObservation.capture(request.snapshot.cut.plan_sha256, item.node,
        state=None, outputs=None) for item in request.snapshot.reads)
    return DecisionFootprint(request.snapshot.cut, request.snapshot.targets, observations)


def bind(request, scope=None, actor=None):
    return SupervisionRequestBinding.bind(request, scope or footprint(),
        actor_id=actor or request.planning_request.actor_id)


def changed(path, value):
    document = original().model_dump(mode='json')
    target = document
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return SupervisionRequest.model_validate_json(json.dumps(document))


def test_projection_and_literal_predecessor_bytes_match_without_private_planning_import():
    request = original()
    assert ScopeExport(footprint()).document() == request.snapshot
    previous_bytes = (FIXTURES / 'planning-request.json').read_bytes()
    assert hashlib.sha256(previous_bytes).hexdigest() == request.planning_request_sha256
    bound = bind(request)
    assert bound.sha256 == (FIXTURES / 'request.sha256').read_text().strip()
    assert bound.document() == request and bind(bound.document()).canonical == bound.canonical
    assert json.loads(previous_bytes) == request.planning_request.model_dump(mode='json')


@pytest.mark.parametrize('path,value,reason', [
    (('snapshot', 'footprint_sha256'), 'f' * 64, 'scope_snapshot_mismatch'),
    (('snapshot', 'relevant_sha256'), 'f' * 64, 'scope_snapshot_mismatch'),
    (('snapshot', 'reads', 0, 'state_sha256'), 'f' * 64, 'scope_snapshot_mismatch'),
    (('reference', 'run_id'), 'other', 'decision_reference_mismatch'),
    (('reference', 'scope', 'project_id'), 'other', 'decision_reference_mismatch'),
    (('planning_request', 'purpose'), 'campaign_proposal', 'wrong_planning_purpose'),
    (('planning_request', 'runtime_cut', 'revision'), 4, 'planning_cut_mismatch'),
    (('planning_request', 'reference', 'scope', 'project_id'), 'other', 'planning_scope_mismatch'),
    (('planning_request', 'context', 'scope', 'project_id'), 'other', 'planning_scope_mismatch'),
    (('policy', 'artifact_id'), 'different', 'planning_policy_mismatch'),
    (('planning_request', 'context', 'prompt', 'scope', 'project_id'), 'other', 'context_artifact_scope_mismatch'),
    (('planning_request_sha256',), 'f' * 64, 'planning_request_digest_mismatch'),
    (('lineage', 'root_request_sha256'), 'f' * 64, 'initial_lineage_mismatch'),
    (('lineage', 'ordinal'), 2, 'successor_lineage_missing'),
])
def test_received_claims_do_not_replace_owned_origin(path, value, reason):
    with pytest.raises(ValueError, match=reason):
        bind(changed(path, value))


def test_actor_and_lineage_shapes_are_distinct_from_auth_and_actual_ancestry():
    with pytest.raises(ValueError, match='planning_actor_mismatch'):
        bind(original(), actor='other')
    data = original().model_dump(mode='json')
    data['lineage'] = {'ordinal': 2, 'root_request_sha256': 'b' * 64, 'parent_request_sha256': 'b' * 64}
    successor = SupervisionRequest.model_validate_json(json.dumps(data))
    assert bind(successor).document() == successor
    data['lineage']['parent_request_sha256'] = 'c' * 64
    with pytest.raises(ValueError, match='first_successor_parent_mismatch'):
        bind(SupervisionRequest.model_validate_json(json.dumps(data)))
    data['lineage']['ordinal'] = 3
    assert bind(SupervisionRequest.model_validate_json(json.dumps(data)))


def test_changed_original_text_requires_its_exact_utf8_hash():
    document = original().model_dump(mode='json')
    document['planning_request']['context']['model']['model_revision'] = 'new-version'
    with pytest.raises(ValueError, match='planning_request_digest_mismatch'):
        bind(SupervisionRequest.model_validate_json(json.dumps(document)))


def test_structurally_valid_large_projection_rejects_instead_of_truncating_request():
    request = original()
    observations = []
    for index in range(128):
        path = ActivationPath.model_validate_json(json.dumps({'schema_version': '2', 'node_id': f'node{index}',
            'occurrences': [{'kind': 'loop', 'node_id': 'container' + 'x' * 119, 'index': number}
                            for number in range(16)]}))
        view = GraphNodeViewV3(activation_id=ActivationAddress(request.snapshot.cut.plan_sha256, path).key,
            path=path, kind='invoke', status='ready', reason_code=None)
        observations.append(NodeObservation.capture(request.snapshot.cut.plan_sha256, view, state=None, outputs=None))
    scope = DecisionFootprint(request.snapshot.cut, (observations[0].identity,), tuple(observations))
    request = request.model_copy(update={'snapshot': ScopeExport(scope).document()})
    with pytest.raises(ValueError, match='supervision_request_size'):
        bind(request, scope)
