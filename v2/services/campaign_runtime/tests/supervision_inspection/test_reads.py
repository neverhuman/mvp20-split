"""Actual Runtime SQL: retained proposal metadata and coherent inspector paging."""

from dataclasses import replace

import pytest
from amphora_campaign_runtime.inspection.cursors import CursorCodec, InspectionError
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.supervision_inspection import SupervisorInspection

from ..supervision_resolution.support import record_response, save_report, setup

KEY = 'supervisor-inspection-test-cursor-key-0000000000000'


def reader(graph, *, clock=None):
    cursors = CursorCodec(KEY) if clock is None else CursorCodec(KEY, ttl_seconds=60, clock=clock)
    return SupervisorInspection(graph.env.engine, cursors)


def test_requests_context_and_winner_reads_expose_metadata_not_payload(graph_env):
    actor, ref, slot, preparer, original, resolver = setup(graph_env)
    inspect = reader(graph_env)
    first = inspect.checkpoints(actor, ref.run_id)
    assert first.total == 1 and first.items[0].winner_kind is None and first.items[0].requests == 1
    token = first.snapshot.snapshot_token
    requests = inspect.requests(actor, ref.run_id, ref.decision_id, snapshot_token=token)
    assert requests.total == 1 and requests.items[0].report_stop_reason is None and requests.items[0].attempts == ()
    context = inspect.context(actor, ref.run_id, ref.decision_id, original.frame.request_sha256, snapshot_token=token)
    assert context.total == 3
    assert [item.kind for item in context.items] == ['included', 'included', 'omitted']
    assert context.items[-1].omission.reason == 'budget'
    first_context = inspect.context(actor, ref.run_id, ref.decision_id, original.frame.request_sha256,
                                    snapshot_token=token, limit=2)
    last_context = inspect.context(actor, ref.run_id, ref.decision_id, original.frame.request_sha256,
        snapshot_token=token, limit=2, cursor=first_context.next_cursor)
    assert last_context.items == context.items[2:] and last_context.next_cursor is None
    assert 'payload_json' not in context.model_dump_json()
    response = record_response(actor, ref, slot, preparer, original)
    save_report(resolver, actor, original, response)
    winner = resolver.resolve(actor, ref, original.frame.request_sha256)
    fresh = inspect.checkpoints(actor, ref.run_id)
    assert fresh.items[0].winner_kind == 'model_accepted'
    requests = inspect.requests(actor, ref.run_id, ref.decision_id, snapshot_token=fresh.snapshot.snapshot_token)
    assert requests.items[0].report_stop_reason == 'proposed' and requests.items[0].attempts[0].status == 'proposed'
    responses = inspect.responses(actor, ref.run_id, ref.decision_id, original.frame.request_sha256,
                                  snapshot_token=fresh.snapshot.snapshot_token)
    assert responses.items[0].selected_by_winner and responses.items[0].status == 'proposed'
    assert responses.items[0].response_sha256 == winner.document().outcome.response_sha256
    assert 'payload_json' not in responses.model_dump_json()


def test_new_response_without_run_revision_change_invalidates_old_snapshot(graph_env):
    actor, ref, slot, preparer, original, _ = setup(graph_env)
    inspect = reader(graph_env)
    first = inspect.checkpoints(actor, ref.run_id)
    record_response(actor, ref, slot, preparer, original)
    fresh = inspect.checkpoints(actor, ref.run_id)
    assert fresh.snapshot.cut.revision == first.snapshot.cut.revision
    assert fresh.snapshot.epoch != first.snapshot.epoch
    with pytest.raises(InspectionError, match='snapshot_unavailable'):
        inspect.requests(actor, ref.run_id, ref.decision_id, snapshot_token=first.snapshot.snapshot_token)


def test_response_pages_and_cursor_survive_replacement_with_same_key(graph_env):
    actor, ref, slot, preparer, original, _ = setup(graph_env)
    record_response(actor, ref, slot, preparer, original, response_id='one')
    record_response(actor, ref, slot, preparer, original, response_id='two')
    inspect = reader(graph_env)
    snapshot = inspect.checkpoints(actor, ref.run_id).snapshot
    page = inspect.responses(actor, ref.run_id, ref.decision_id, original.frame.request_sha256,
                             snapshot_token=snapshot.snapshot_token, limit=1)
    assert page.total == 2 and page.next_cursor and page.items[0].response_id == 'one'
    replacement = reader(graph_env)
    second = replacement.responses(actor, ref.run_id, ref.decision_id, original.frame.request_sha256,
        snapshot_token=snapshot.snapshot_token, limit=1, cursor=page.next_cursor)
    assert second.items[0].response_id == 'two' and second.next_cursor is None
    assert not any(item.selected_by_winner for item in (*page.items, *second.items))
    with pytest.raises(InspectionError, match='cursor_mismatch'):
        inspect.context(actor, ref.run_id, ref.decision_id, original.frame.request_sha256,
            snapshot_token=snapshot.snapshot_token, cursor=page.next_cursor)


@pytest.mark.parametrize('variant,expected', [('invalid', 'repair'), ('profile', 'fallback')])
def test_rejected_response_disposition_is_distinct_from_provider_status(graph_env, variant, expected):
    actor, ref, slot, preparer, original, resolver = setup(graph_env)
    response = record_response(actor, ref, slot, preparer, original, variant=variant)
    save_report(resolver, actor, original, response)
    resolver.resolve(actor, ref, original.frame.request_sha256)
    inspect = reader(graph_env)
    snapshot = inspect.checkpoints(actor, ref.run_id).snapshot
    page = inspect.requests(actor, ref.run_id, ref.decision_id, snapshot_token=snapshot.snapshot_token)
    assert page.items[0].disposition == expected and page.items[0].disposition_reason is not None
    responses = inspect.responses(actor, ref.run_id, ref.decision_id, original.frame.request_sha256,
                                  snapshot_token=snapshot.snapshot_token)
    assert responses.items[0].status in {'invalid', 'policy_rejected'} and not responses.items[0].selected_by_winner


def test_missing_report_fallback_and_empty_requests_remain_explicit(graph_env):
    actor, ref, _, preparer, _, resolver = setup(graph_env, prepare=False)
    inspect = reader(graph_env)
    snapshot = inspect.checkpoints(actor, ref.run_id).snapshot
    assert inspect.requests(actor, ref.run_id, ref.decision_id, snapshot_token=snapshot.snapshot_token).total == 0
    original = preparer.prepare(actor, ref)
    save_report(resolver, actor, original)
    resolver.resolve(actor, ref, original.frame.request_sha256)
    page = inspect.checkpoints(actor, ref.run_id)
    assert page.items[0].winner_kind == 'fallback' and page.items[0].winner_reason == 'checkpoint_provider_unconfigured'
    requests = inspect.requests(actor, ref.run_id, ref.decision_id, snapshot_token=page.snapshot.snapshot_token)
    assert requests.items[0].attempts == () and requests.items[0].report_stop_reason == 'provider_unconfigured'


def test_scope_permissions_limits_and_expiring_tokens_fail_closed(graph_env):
    actor, ref, _, _, original, _ = setup(graph_env)
    clock = [100]
    inspect = reader(graph_env, clock=lambda: clock[0])
    token = inspect.checkpoints(actor, ref.run_id).snapshot.snapshot_token
    with pytest.raises(TransitionError, match='access_denied'):
        inspect.checkpoints(replace(actor, actions=frozenset()), ref.run_id)
    foreign = replace(actor, scope=actor.scope.model_copy(update={'project_id': 'unknown-project'}))
    with pytest.raises(InspectionError, match='run_unavailable'):
        inspect.checkpoints(foreign, ref.run_id)
    for limit in (0, 11, True):
        with pytest.raises(InspectionError, match='invalid_page_request'):
            inspect.checkpoints(actor, ref.run_id, limit=limit)
    with pytest.raises(InspectionError, match='invalid_cursor'):
        inspect.requests(actor, ref.run_id, ref.decision_id, snapshot_token=token + 'tampered')
    with pytest.raises(InspectionError, match='supervision_checkpoint_unavailable'):
        inspect.requests(actor, ref.run_id, 'unknown', snapshot_token=token)
    with pytest.raises(InspectionError, match='supervision_request_unavailable'):
        inspect.context(actor, ref.run_id, ref.decision_id, 'f' * 64, snapshot_token=token)
    clock[0] = 161
    with pytest.raises(InspectionError, match='cursor_expired'):
        inspect.responses(actor, ref.run_id, ref.decision_id, original.frame.request_sha256, snapshot_token=token)
