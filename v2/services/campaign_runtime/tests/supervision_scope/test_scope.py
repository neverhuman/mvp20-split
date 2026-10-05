"""Decision interference and stale inputs, independently specified scenarios."""

from dataclasses import FrozenInstanceError, replace

import pytest
from amphora_campaign_runtime.compiler.addresses import ActivationAddress
from amphora_campaign_runtime.supervision_scope import (
    DecisionFootprint,
    NodeObservation,
)
from amphora_contracts_campaigns import ActivationPath
from amphora_contracts_graph_runtime import GraphNodeViewV3, GraphReadCut

PLAN = 'a' * 64


def cut(**changes):
    return GraphReadCut.model_validate({'scope': {'tenant_id': 'tenant', 'project_id': 'project'},
        'run_id': 'run', 'plan_sha256': PLAN, 'revision': 10, 'frontier_revision': 5, **changes})


def node(name, *, status='ready', kind='invoke', occurrences=(), state=None, outputs=None, plan=PLAN):
    path = ActivationPath.model_validate({'schema_version': '2', 'node_id': name, 'occurrences': tuple(occurrences)})
    view = GraphNodeViewV3(activation_id=ActivationAddress(plan, path).key, path=path,
                         kind=kind, status=status, reason_code=None)
    return NodeObservation.capture(plan, view, state=state, outputs=outputs)


def footprint(*targets, reads=(), origin=None):
    return DecisionFootprint(origin or cut(), tuple(item.identity for item in targets), (*targets, *reads))


def test_disjoint_lanes_share_reads_but_not_read_write_interference():
    a, b, shared = node('a'), node('b'), node('measurement', status='succeeded')
    left, right = footprint(a, reads=(shared,)), footprint(b, reads=(shared,))
    assert not left.overlaps(right) and not right.overlaps(left)
    reader = footprint(b, reads=(a,))
    assert left.overlaps(reader) and reader.overlaps(left)
    assert left.overlaps(footprint(a))


def test_same_plan_in_other_run_or_tenant_does_not_conflict():
    a = node('a')
    original = footprint(a)
    assert not original.overlaps(footprint(a, origin=cut(run_id='other')))
    assert not original.overlaps(footprint(a, origin=cut(scope={'tenant_id': 'other', 'project_id': 'project'})))
    b = node('a', plan='b' * 64)
    with pytest.raises(ValueError, match='run_plan_mismatch'):
        original.overlaps(footprint(b, origin=cut(plan_sha256='b' * 64)))


@pytest.mark.parametrize('kind', ['loop', 'scatter'])
def test_concrete_occurrences_are_distinct_targets(kind):
    first = {'kind': kind, 'node_id': 'container', 'index': 0}
    if kind == 'scatter':
        first['membership_sha256'] = 'b' * 64
    second = {**first, 'index': 1}
    a, b = node('score', occurrences=(first,)), node('score', occurrences=(second,))
    assert a.identity != b.identity
    assert not footprint(a).overlaps(footprint(b))
    if kind == 'scatter':
        c = node('score', occurrences=({**first, 'membership_sha256': 'c' * 64},))
        assert not footprint(a).overlaps(footprint(c))


def test_order_independent_identity_keeps_cut_provenance_out_of_staleness():
    a, b = node('a'), node('b')
    old = footprint(a, b)
    newer = footprint(b, a, origin=cut(revision=20, frontier_revision=9))
    assert old.cut != newer.cut
    assert old.sha256 == newer.sha256 and old.relevant_sha256 == newer.relevant_sha256
    assert not old.compare(newer.cut, (b, a, node('unrelated', status='succeeded'))).stale


def test_selected_output_state_status_and_absence_are_relevant():
    a, measurement = node('a'), node('measurement', status='succeeded', outputs={'value': 1})
    original = footprint(a, reads=(measurement,))
    for changed in (node('measurement', status='succeeded', outputs={'value': 2}),
                    node('measurement', status='succeeded', outputs={'value': 1}, state={'revision': 2})):
        result = original.compare(cut(revision=11), (a, changed))
        assert result.stale and result.changed == (measurement.identity,) and result.missing == ()
    issued = node('a', status='issued')
    assert original.compare(cut(revision=11), (issued, measurement)).changed == (a.identity,)
    missing = original.compare(cut(), (a,))
    assert missing.missing == (measurement.identity,) and not missing.changed
    assert original.compare(cut(), ()).missing == tuple(sorted((a.identity, measurement.identity)))
    assert original.relevant_sha256 != footprint(a, reads=(changed,)).relevant_sha256


@pytest.mark.parametrize('changes,reason', [({'run_id': 'other'}, 'current_cut_mismatch'),
    ({'plan_sha256': 'b' * 64}, 'current_cut_mismatch'), ({'revision': 9}, 'older_current_cut'),
    ({'frontier_revision': 4}, 'older_current_cut')])
def test_wrong_or_older_cut_cannot_be_fresh(changes, reason):
    a = node('a')
    with pytest.raises(ValueError, match=reason):
        footprint(a).compare(cut(**changes), (a,))


def test_observation_owns_original_bytes_and_rejects_forged_identity():
    state, outputs = {'x': [1]}, {'y': 2}
    a = node('a', state=state, outputs=outputs)
    sha = a.sha256
    state['x'].append(3)
    outputs['y'] = 8
    assert a.sha256 == sha and a.state_json == b'{"x":[1]}'
    with pytest.raises(FrozenInstanceError):
        a.plan_sha256 = 'b' * 64
    with pytest.raises(ValueError, match='activation_identity_mismatch'):
        replace(a, view=a.view.model_copy(update={'activation_id': 'f' * 64}))


@pytest.mark.parametrize('state,reason', [({1: 'coerced'}, 'non_string_json_key'),
    ({'x': (1, 2)}, 'unsupported_json_value'), ({'x': float('nan')}, 'Out of range'),
    ({'x': 'z' * 1048576}, 'node_observation_limit')])
def test_invalid_or_oversize_observation_is_not_silently_normalized(state, reason):
    with pytest.raises(ValueError, match=reason):
        node('a', state=state)


@pytest.mark.parametrize('raw', [b'{ "x":1}', b'{"x":1,"x":1}', b'1.0e0'])
def test_noncanonical_bytes_reject(raw):
    with pytest.raises(ValueError, match='noncanonical_observation'):
        replace(node('a'), state_json=raw)


@pytest.mark.parametrize('status', ['issued', 'succeeded', 'failed', 'blocked', 'skipped'])
def test_already_used_or_terminal_target_is_unavailable(status):
    with pytest.raises(ValueError, match='target_unavailable'):
        footprint(node('a', status=status))


def test_target_contract_requires_observed_unique_unmaterialized_invoke():
    a, b = node('a'), node('b')
    cases = [((), (a,), 'target_count'), ((a.identity,) * 2, (a,), 'duplicate_target'),
             ((a.identity,), (b,), 'target_observation_missing'),
             ((a.identity,), (a, a), 'duplicate_observation'),
             ((a.identity,), (), 'observation_count'),
             (('wrong',), (a,), 'invalid_digest'),
             ((a.identity,), ('not-an-observation',), 'observation_type')]
    for targets, observations, reason in cases:
        with pytest.raises(ValueError, match=reason):
            DecisionFootprint(cut(), targets, observations)
    with pytest.raises(ValueError, match='target_unavailable'):
        footprint(node('branch', kind='branch'))
    assert footprint(node('waiting', status='waiting'))


def test_scope_and_compare_reject_wrong_plan_duplicate_or_mutable_input():
    a, other = node('a'), node('other', plan='b' * 64)
    with pytest.raises(ValueError, match='observation_plan_mismatch'):
        footprint(a, reads=(other,))
    for records, reason in [([a], 'observation_count'), ((a, a), 'duplicate_observation'),
                            ((other,), 'observation_plan_mismatch')]:
        with pytest.raises(ValueError, match=reason):
            footprint(a).compare(cut(), records)
    with pytest.raises(ValueError, match='immutable_bytes_required'):
        replace(a, state_json=bytearray(b'null'))


def test_fixed_collection_and_aggregate_byte_limits():
    nodes = tuple(node(f'n{i}') for i in range(257))
    with pytest.raises(ValueError, match='target_count'):
        footprint(*nodes[:65])
    with pytest.raises(ValueError, match='observation_count'):
        footprint(nodes[0], reads=nodes[1:])
    large = tuple(node(f'n{i}', state={'data': 'x' * 1000000}) for i in range(9))
    with pytest.raises(ValueError, match='scope_observation_limit'):
        footprint(large[0], reads=large[1:])
