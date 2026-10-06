"""Conversion-boundary identity, conservative conflicts and old-profile isolation."""

from dataclasses import replace

import pytest
from amphora_campaign_runtime.compiler.addresses import ActivationAddress
from amphora_campaign_runtime.supervision_requests.projection import ScopeExport
from amphora_campaign_runtime.supervision_scope import (
    DecisionFootprint,
    NodeObservation,
)
from amphora_campaign_runtime.supervision_scope.checkpoints import (
    CheckpointFootprint,
    CheckpointTarget,
)
from amphora_contracts_campaigns import ActivationPath
from amphora_contracts_graph_runtime import GraphNodeViewV3, GraphReadCut

PLAN = 'a' * 64


def cut(**changes):
    return GraphReadCut.model_validate({'scope': {'tenant_id': 'tenant', 'project_id': 'project'},
        'run_id': 'run', 'plan_sha256': PLAN, 'revision': 10, 'frontier_revision': 5, **changes})


def node(name='parameters', *, kind='artifact_materialize', status='ready', occurrences=(), state=None):
    path = ActivationPath(schema_version='2', node_id=name, occurrences=occurrences)
    view = GraphNodeViewV3(activation_id=ActivationAddress(PLAN, path).key, path=path,
                         kind=kind, status=status, reason_code=None)
    return NodeObservation.capture(PLAN, view, state=state, outputs=None)


def materialization(observation=None, *, fields=('temperature',), reads=(), origin=None):
    observation = observation or node()
    return CheckpointFootprint(origin or cut(), (CheckpointTarget.materialize(observation, fields),),
                               (observation, *reads))


def test_field_selection_is_fingerprinted_and_order_independent():
    first = materialization(fields=('temperature', 'pressure'))
    same = materialization(fields=('pressure', 'temperature'), origin=cut(revision=11))
    different = materialization(fields=('temperature',))
    assert first.sha256 == same.sha256 and first.relevant_sha256 == same.relevant_sha256
    assert first.sha256 != different.sha256 and first.relevant_sha256 != different.relevant_sha256
    assert first.overlaps(different) and different.overlaps(first)
    assert first.record['profile'] == 'runtime-supervision-footprint.v2'


def test_disjoint_fields_still_compete_for_one_conversion():
    first, second = materialization(fields=('temperature',)), materialization(fields=('pressure',))
    assert first.overlaps(second) and second.overlaps(first)


def test_old_profile_rejects_materialization_and_new_profile_cannot_export_as_old():
    observation = node()
    with pytest.raises(ValueError, match='target_unavailable'):
        DecisionFootprint(cut(), (observation.identity,), (observation,))
    with pytest.raises(ValueError, match='scope_profile_mismatch'):
        ScopeExport(materialization()).document()
    review = node('tool', kind='invoke')
    old = DecisionFootprint(cut(), (review.identity,), (review,))
    new = CheckpointFootprint(cut(), (CheckpointTarget.review(review),), (review,))
    assert old.sha256 != new.sha256 and old.relevant_sha256 != new.relevant_sha256
    assert old.overlaps(new) and new.overlaps(old)
    assert ScopeExport(old).document().schema_version == '1'


def test_cross_profile_read_write_conflicts_and_shared_read_independence():
    review, conversion, shared = node('tool', kind='invoke'), node(), node('data', status='succeeded')
    old = DecisionFootprint(cut(), (review.identity,), (review, shared))
    new = materialization(conversion, reads=(shared,))
    assert not old.overlaps(new) and not new.overlaps(old)
    reader = materialization(conversion, reads=(review, shared))
    assert old.overlaps(reader) and reader.overlaps(old)
    assert not new.overlaps(materialization(origin=cut(run_id='other')))
    other_plan = replace(old, cut=cut(plan_sha256='b' * 64), observations=(
        NodeObservation.capture('b' * 64, GraphNodeViewV3(
            activation_id=ActivationAddress('b' * 64, review.view.path).key, path=review.view.path,
            kind='invoke', status='ready', reason_code=None), state=None, outputs=None),),
        targets=(ActivationAddress('b' * 64, review.view.path).key,))
    with pytest.raises(ValueError, match='run_plan_mismatch'):
        new.overlaps(other_plan)


@pytest.mark.parametrize('kind', ['loop', 'scatter'])
def test_distinct_iteration_and_scatter_members_do_not_share_checkpoint(kind):
    occurrence = {'kind': kind, 'node_id': 'container', 'index': 0}
    if kind == 'scatter':
        occurrence['membership_sha256'] = 'b' * 64
    first = materialization(node(occurrences=(occurrence,)))
    second = materialization(node(occurrences=({**occurrence, 'index': 1},)))
    assert first.sha256 != second.sha256 and not first.overlaps(second)


@pytest.mark.parametrize('status', ['issued', 'succeeded', 'failed', 'blocked', 'skipped'])
def test_opened_or_terminal_conversion_is_not_available(status):
    with pytest.raises(ValueError, match='target_unavailable'):
        materialization(node(status=status))


@pytest.mark.parametrize('kind,fields,reason', [
    ('artifact_project', (), 'checkpoint_target_kind'),
    ('invoke', ('temperature',), 'checkpoint_fields_for_kind'),
    ('artifact_materialize', (), 'checkpoint_fields_for_kind'),
    ('artifact_materialize', ['temperature'], 'checkpoint_fields_immutable'),
    ('artifact_materialize', ('temperature',) * 2, 'duplicate_checkpoint_field'),
    ('artifact_materialize', tuple(str(i) for i in range(65)), 'checkpoint_field_count'),
    ('artifact_materialize', (1,), 'checkpoint_field_name'),
    ('artifact_materialize', ('',), 'String should'),
])
def test_invalid_targets_reject(kind, fields, reason):
    with pytest.raises(ValueError, match=reason):
        CheckpointTarget(node().identity, kind, fields)


def test_mismatched_kind_missing_duplicate_or_untyped_targets_reject():
    observation = node()
    target = CheckpointTarget.materialize(observation, ('temperature',))
    for targets, reads, reason in [
        ((), (observation,), 'target_count'),
        ((target,) * 2, (observation,), 'duplicate_target'),
        ((target,), (node('other'),), 'target_observation_missing'),
        (('target',), (observation,), 'checkpoint_target_type'),
        ((CheckpointTarget.review(observation),), (observation,), 'checkpoint_target_mismatch'),
    ]:
        with pytest.raises(ValueError, match=reason):
            CheckpointFootprint(cut(), targets, reads)
    with pytest.raises(ValueError, match='checkpoint_target_mismatch'):
        target.verify(node('other'))


def test_selected_changes_stale_but_unrelated_progress_does_not():
    footprint = materialization()
    assert not footprint.compare(cut(revision=99), (node(), node('unrelated'))).stale
    assert footprint.compare(cut(), (node(state={'changed': True}),)).changed == footprint.targets
    assert footprint.compare(cut(), ()).missing == footprint.targets
    for origin, reason in [(cut(run_id='other'), 'current_cut_mismatch'),
                            (cut(revision=9), 'older_current_cut')]:
        with pytest.raises(ValueError, match=reason):
            footprint.compare(origin, (node(),))
    with pytest.raises(ValueError, match='observation_count'):
        footprint.compare(cut(), [node()])


def test_multiple_targets_and_reads_sort_without_losing_identity():
    a, b = node('a'), node('b', kind='invoke', status='waiting')
    targets = (CheckpointTarget.materialize(a, ('temperature',)), CheckpointTarget.review(b))
    first = CheckpointFootprint(cut(), targets, (a, b))
    second = CheckpointFootprint(cut(), targets[::-1], (b, a))
    assert first.sha256 == second.sha256 and first.targets == tuple(sorted((a.identity, b.identity)))
