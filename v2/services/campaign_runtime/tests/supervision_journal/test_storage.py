"""Actual PostgreSQL producer checks and atomic immutable request history."""

import copy
import hashlib
import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.graph_inspection.policy import node_view
from amphora_campaign_runtime.supervision_journal import RequestFrame
from amphora_campaign_runtime.supervision_journal.storage import (
    RequestJournal,
    StoredRequest,
)
from amphora_campaign_runtime.supervision_requests import ScopeExport
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_campaign_runtime.supervision_scope import (
    DecisionFootprint,
    NodeObservation,
)
from amphora_contracts_graph_runtime import GraphReadCut
from amphora_contracts_supervision import SupervisionRequest, parse_supervision_command
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..compiler.conftest import definition
from ..supervision_requests.test_binding import original
from .test_series import next_frame


def command(frame, key=None):
    request = frame.request
    return parse_supervision_command('planning.supervision.request', json.dumps({
        'encoding': 'amphora-command-v2', 'identity': {'scope': request.reference.scope.model_dump(),
        'actor_id': request.planning_request.actor_id, 'command_family': 'planning.supervision.request',
        'command_id': key or f'request-{request.lineage.ordinal}'}, 'payload': request.model_dump(mode='json')})).canonical_bytes


def setup(g, *, nested=False):
    e = g.env
    e.principal = replace(e.principal, actions=e.principal.actions | {'supervise_prepare'})
    raw = g.source.raw[3 if nested == 'loop' else 2 if nested else 1]
    raw['scope'] = e.principal.scope.model_dump(mode='json')
    if nested == 'loop':
        loop = raw['body']['nodes'][0]
        parameter = copy.deepcopy(g.raw['body']['inputs'][0])
        raw['body']['inputs'].append(parameter)
        loop['body']['inputs'].append(parameter)
        loop['captures'] = [{'port': 'parameters', 'source': {'kind': 'input', 'name': 'parameters'}}]
        loop['body']['nodes'].insert(0, copy.deepcopy(g.raw['body']['nodes'][0]))
        loop['body']['edges'] = [{'source': 'affine', 'target': 'finish', 'route': 'next'}]
    reviewed = ReviewedPlan.compile(definition(raw), g.source.tools, g.source.schemas)
    payload = {**g.payload, 'plan_sha256': reviewed.plan.sha256,
        'inputs': [*g.payload['inputs'], {'port': 'flag', 'value': {'kind': 'boolean', 'value': True}}]}
    if nested:
        payload['inputs'] = [{'port': 'items', 'value': {'kind': 'collection',
            'items': [g.payload['inputs'][0]['value']]}}]
    if nested == 'loop':
        payload['inputs'] = g.payload['inputs']
    admission = GraphAdmission(e.engine, PlanCatalog([reviewed]))
    run = admission.admit(e.principal, g.command('graph.admit', payload)).outcome.committed.object_id
    if nested:
        GraphAdvancer(e.engine).advance(e.principal, g.command('graph.advance',
            {'run_id': run, 'max_transitions': 1 if nested == 'loop' else 2}))
    params = RequestJournal.params(e.principal, run, 'decision-1')
    with e.engine.connect() as conn:
        row = conn.execute(text('SELECT r.revision,g.plan_sha256,g.frontier_revision,'
            'floor(extract(epoch from g.deadline)*1000)::bigint AS deadline FROM runtime.runs r '
            'JOIN runtime.graph_runs g USING(tenant_id,project_id,run_id) '
            'WHERE r.tenant_id=:tenant AND r.project_id=:project AND r.run_id=:run'), params).mappings().one()
        node = conn.execute(text("SELECT * FROM runtime.graph_nodes WHERE tenant_id=:tenant AND project_id=:project "
            "AND run_id=:run AND kind='invoke' ORDER BY priority LIMIT 1"), params).mappings().one()
        extra = conn.execute(text("SELECT * FROM runtime.graph_nodes WHERE tenant_id=:tenant AND project_id=:project "
            "AND run_id=:run AND kind='branch' ORDER BY priority LIMIT 1"), params).mappings().one_or_none()
    cut = GraphReadCut(scope=e.principal.scope, run_id=run, plan_sha256=row['plan_sha256'],
                       revision=row['revision'], frontier_revision=row['frontier_revision'])
    observation = NodeObservation.capture(cut.plan_sha256, node_view(node), state=node['state'], outputs=node['outputs'])
    observations = (observation,)
    if extra is not None:
        observations += (NodeObservation.capture(cut.plan_sha256, node_view(extra), state=extra['state'], outputs=extra['outputs']),)
    footprint = DecisionFootprint(cut, (observation.identity,), observations)
    data = original().model_dump(mode='json')
    def scoped(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == 'scope':
                    value[key] = e.principal.scope.model_dump(mode='json')
                else:
                    scoped(item)
        elif isinstance(value, list):
            for item in value:
                scoped(item)
    scoped(data)
    data['reference']['run_id'] = run
    data['snapshot'] = ScopeExport(footprint).document().model_dump(mode='json')
    data['planning_request']['runtime_cut'] = cut.model_dump(mode='json')
    data['deadline_unix_ms'] = row['deadline']
    request = SupervisionRequest.model_validate_json(json.dumps(data))
    request = request.model_copy(update={'planning_request_sha256': hashlib.sha256(encoded(request.planning_request)).hexdigest()})
    frame = RequestFrame.capture(request, footprint, prepared_by=e.principal.actor_id,
                                 planning_actor=request.planning_request.actor_id)
    journal = RequestJournal(e.engine, {(params['tenant'], params['project'], e.principal.actor_id):
                                        request.planning_request.actor_id})
    return e, journal, frame, params


def test_exact_restart_replay_and_bounded_successor(graph_env):
    e, journal, frame, params = setup(graph_env)
    first = journal.prepare(e.principal, frame, command(frame))
    replacement = RequestJournal(e.engine, journal.planning_actors)
    assert replacement.prepare(e.principal, frame, command(frame)) == first
    assert replacement.series(e.principal, params['run'], params['decision']) == (first,)
    second = next_frame(frame, prepared_by=e.principal.actor_id)
    second_record = replacement.prepare(e.principal, second, command(second))
    assert replacement.series(e.principal, params['run'], params['decision']) == (first, second_record)
    with pytest.raises(ValueError, match='request_identity_conflict'):
        replacement.prepare(e.principal, frame, command(frame, 'different'))
    with e.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run"), params)
    assert replacement.prepare(e.principal, frame, command(frame)) == first


@pytest.mark.parametrize('fault,reason', [('state', 'selected_observation_changed'),
    ('inactive', 'inactive_target_scope'), ('deadline', 'supervision_deadline_unavailable')])
def test_actual_state_not_received_hash_controls_fresh_storage(graph_env, fault, reason):
    e, journal, frame, params = setup(graph_env)
    with e.engine.begin() as conn:
        if fault == 'state':
            conn.execute(text('UPDATE runtime.graph_nodes SET state=CAST(:state AS jsonb) WHERE tenant_id=:tenant '
                'AND project_id=:project AND run_id=:run'), {**params, 'state': json.dumps({'changed': True})})
        elif fault == 'inactive':
            conn.execute(text("UPDATE runtime.graph_scopes SET status='blocked' WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run"), params)
    if fault == 'deadline':
        request = frame.request.model_copy(update={'deadline_unix_ms': 1})
        frame = RequestFrame.capture(request, frame.footprint(), prepared_by=e.principal.actor_id,
                                     planning_actor=request.planning_request.actor_id)
    with pytest.raises(ValueError, match=reason):
        journal.prepare(e.principal, frame, command(frame))
    assert journal.series(e.principal, params['run'], params['decision']) == ()


def test_unrelated_revision_does_not_stale_selected_nodes(graph_env):
    e, journal, frame, params = setup(graph_env)
    with e.engine.begin() as conn:
        conn.execute(text('UPDATE runtime.runs SET revision=revision+1 WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run'), params)
    assert journal.prepare(e.principal, frame, command(frame)).frame == frame


def test_rollback_original_actor_and_read_scope(graph_env, monkeypatch):
    e, journal, frame, params = setup(graph_env)
    with pytest.raises(ValueError, match='planning_delegation_unavailable'):
        RequestJournal(e.engine, {}).prepare(e.principal, frame, command(frame))
    with pytest.raises(ValueError, match='access_denied'):
        journal.prepare(replace(e.principal, actions=frozenset({'read'})), frame, command(frame))
    original_reader = StoredRequest.from_row
    def fail(row):
        raise RuntimeError('after_both_inserts')
    monkeypatch.setattr(StoredRequest, 'from_row', fail)
    with pytest.raises(RuntimeError, match='after_both_inserts'):
        journal.prepare(e.principal, frame, command(frame))
    monkeypatch.setattr(StoredRequest, 'from_row', original_reader)
    assert journal.series(e.principal, params['run'], params['decision']) == ()
    saved = journal.prepare(e.principal, frame, command(frame))
    foreign = replace(e.principal, scope=e.principal.scope.model_copy(update={'project_id': 'foreign'}))
    assert journal.series(foreign, params['run'], params['decision']) == ()
    assert journal.series(e.principal, params['run'], params['decision']) == (saved,)
    for table in ('supervision_requests', 'supervision_outbox'):
        for verb in ('DELETE FROM', 'UPDATE'):
            statement = f'{verb} runtime.{table}'
            if verb == 'UPDATE':
                statement += ' SET created_at=clock_timestamp()'
            with pytest.raises(DBAPIError), e.engine.begin() as conn:
                conn.execute(text(statement + ' WHERE tenant_id=:tenant AND project_id=:project'), params)


def test_materialized_target_cannot_be_reopened_by_public_status(graph_env):
    e, journal, frame, params = setup(graph_env)
    GraphAdvancer(e.engine).advance(e.principal, graph_env.command('graph.advance', {'run_id': params['run']}))
    with e.engine.begin() as conn:
        conn.execute(text('UPDATE runtime.graph_nodes SET status=:status WHERE tenant_id=:tenant AND project_id=:project '
            'AND run_id=:run AND activation_id=:activation'), {**params,
            'status': next(item.view.status for item in frame.footprint().observations
                           if item.identity in frame.footprint().targets), 'activation': frame.footprint().targets[0]})
    with pytest.raises(ValueError, match='target_already_materialized'):
        journal.prepare(e.principal, frame, command(frame))


@pytest.mark.parametrize('fault', [None, 'parent', 'membership', 'ancestor'])
def test_actual_nested_membership_and_all_ancestors(graph_env, fault):
    e, journal, frame, params = setup(graph_env, nested=True)
    assert frame.footprint().observations[0].view.path.occurrences
    with e.engine.begin() as conn:
        if fault == 'parent':
            conn.execute(text("UPDATE runtime.graph_nodes SET status='skipped' WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run AND kind='scatter'"), params)
        elif fault == 'membership':
            conn.execute(text("UPDATE runtime.graph_nodes SET state=jsonb_set(state,'{membership_sha256}',CAST(:digest AS jsonb)) "
                "WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run AND kind='scatter'"),
                {**params, 'digest': json.dumps('f' * 64)})
        elif fault == 'ancestor':
            conn.execute(text("UPDATE runtime.graph_scopes SET status='blocked' WHERE tenant_id=:tenant AND project_id=:project "
                "AND run_id=:run AND parent_activation_id IS NULL"), params)
    if fault:
        expected = {'parent': 'inactive_target_parent', 'membership': 'target_occurrence_mismatch',
                    'ancestor': 'inactive_target_scope'}[fault]
        with pytest.raises(ValueError, match=expected):
            journal.prepare(e.principal, frame, command(frame))
    else:
        assert journal.prepare(e.principal, frame, command(frame)).frame == frame


def test_foreign_run_fk_and_command_identity_collision_rollback(graph_env):
    e, journal, frame, params = setup(graph_env)
    journal.prepare(e.principal, frame, command(frame))
    second = next_frame(frame, prepared_by=e.principal.actor_id)
    with pytest.raises(DBAPIError):
        journal.prepare(e.principal, second, command(second, 'request-1'))
    assert len(journal.series(e.principal, params['run'], params['decision'])) == 1
    with pytest.raises(DBAPIError), e.engine.begin() as conn:
        conn.execute(text('''INSERT INTO runtime.supervision_requests
            (tenant_id,project_id,run_id,decision_id,ordinal,plan_sha256,prepared_by,planning_actor,
             engagement_id,checkpoint_id,request_sha256,frame_sha256,root_request_sha256,
             parent_request_sha256,canonical_frame)
            SELECT tenant_id,'foreign',run_id,decision_id,ordinal,plan_sha256,prepared_by,planning_actor,
             engagement_id,checkpoint_id,request_sha256,frame_sha256,root_request_sha256,
             parent_request_sha256,canonical_frame FROM runtime.supervision_requests
             WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run'''), params)


@pytest.mark.parametrize('changed', [False, True])
def test_actual_loop_iteration_membership(graph_env, changed):
    e, journal, frame, params = setup(graph_env, nested='loop')
    if changed:
        with e.engine.begin() as conn:
            conn.execute(text("UPDATE runtime.graph_nodes SET state=jsonb_set(state,'{iteration}','1') "
                "WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run AND kind='iterate'"), params)
        with pytest.raises(ValueError, match='target_occurrence_mismatch'):
            journal.prepare(e.principal, frame, command(frame))
    else:
        assert journal.prepare(e.principal, frame, command(frame)).frame == frame
