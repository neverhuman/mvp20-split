"""Actual run-locked slot creation, immutable replay and bounded eligibility."""

import copy
import json
import time
import uuid
from datetime import timedelta

import pytest
from amphora_campaign_runtime.coordinator import ReviewedPlan
from amphora_campaign_runtime.coordinator.frontier import FrontierPlanner, ScopeAddress
from amphora_campaign_runtime.coordinator.storage import GraphStorage
from amphora_campaign_runtime.coordinator.values import BoundValues
from amphora_campaign_runtime.persistence.commands import CommandStore
from amphora_campaign_runtime.supervision_checkpoints.seed import CheckpointSeed
from amphora_campaign_runtime.supervision_checkpoints.storage import CheckpointStore
from amphora_campaign_runtime.supervision_checkpoints.values import ValueCheckpointSeed
from amphora_campaign_runtime.supervision_policy import PolicyRecord, ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.storage import PolicyPins
from amphora_contracts_campaigns import ActivationPath
from amphora_contracts_graph_runtime import AdmitGraphRun
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..compiler.conftest import definition
from ..supervision_policy.test_admission import command, reviewed


def admitted(graph, *, two=False, limit=5):
    if two:
        raw = copy.deepcopy(graph.raw)
        node = copy.deepcopy(next(item for item in raw['body']['nodes'] if item['kind'] == 'invoke'))
        node['node_id'] = 'other'
        finish = next(item['node_id'] for item in raw['body']['nodes'] if item['kind'] == 'finish')
        raw['body']['nodes'].append(node)
        raw['body']['edges'].append({'source': 'other', 'target': finish})
        graph.entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
        graph.payload['plan_sha256'] = graph.entry.plan.sha256
    policy = reviewed(graph)
    data = policy.document().model_dump(mode='json')
    data['ceilings']['max_checkpoints'] = limit
    if two:
        second = copy.deepcopy(data['checkpoints'][0])
        second['checkpoint_id'] = 'other-review'
        second['target']['node_id'] = 'other'
        data['checkpoints'].append(second)
    policy = ReviewedPolicy.bind(graph.entry.plan, PolicyRecord.model_validate_json(json.dumps(data)))
    # Storage fixture explicitly seeds the pre-dispatch transaction boundary; separate
    # integration tests exercise GraphAdmission's automatic checkpoint creation.
    original = command(graph, policy)
    CommandStore(graph.env.engine).register(original)
    params = {'tenant': graph.env.principal.scope.tenant_id, 'project': graph.env.principal.scope.project_id,
              'run': uuid.uuid4().hex, 'digest': graph.entry.plan.sha256}
    admission = AdmitGraphRun.model_validate_json(json.dumps(graph.payload))
    with graph.env.engine.begin() as conn:
        GraphStorage.retain_plan(conn, params, graph.entry)
        conn.execute(text("INSERT INTO runtime.runs (tenant_id,project_id,run_id,fixture_id,plan_sha256,"
            "input_snapshot,status,budget_limit,execution_mode) VALUES (:tenant,:project,:run,'fixture',:digest,"
            "'{}','running',2,'graph')"), params)
        deadline = conn.execute(text('SELECT clock_timestamp()')).scalar_one() + timedelta(seconds=admission.limits.deadline_seconds)
        conn.execute(text('INSERT INTO runtime.graph_runs (tenant_id,project_id,run_id,plan_sha256,inputs,'
            'max_activations,deadline) VALUES (:tenant,:project,:run,:digest,CAST(:inputs AS jsonb),100,:deadline)'),
            {**params, 'inputs': json.dumps([value.model_dump(mode='json') for value in admission.inputs]), 'deadline': deadline})
        PolicyPins.pin(conn, params['run'], original, policy)
        address = ScopeAddress(graph.entry.plan.sha256)
        GraphStorage.create_scope(conn, params, address, BoundValues(admission.inputs), FrontierPlanner().scope(graph.entry.plan, address))
    paths = [ActivationPath(schema_version='2', node_id=rule.target.node_id, occurrences=())
             for rule in policy.document().checkpoints]
    return params, paths


def test_original_slot_survives_progress_and_connection_replacement_without_deadline_refresh(graph_env):
    graph = graph_env
    params, paths = admitted(graph)
    with graph.env.engine.begin() as conn:
        original = CheckpointStore.ensure(conn, params, paths[0])
        assert original.created and original.checkpoint.eligibility == 'requestable'
        conn.execute(text('UPDATE runtime.runs SET revision=revision+1 WHERE run_id=:run'), params)
    with graph.env.engine.begin() as conn:
        replay = CheckpointStore.ensure(conn, params, paths[0])
        assert not replay.created and replay.checkpoint == original.checkpoint
        assert conn.execute(text('SELECT count(*) FROM runtime.activations WHERE run_id=:run'), params).scalar_one() == 0
        for statement in ['UPDATE runtime.supervision_checkpoints SET ordinal=ordinal',
                          'DELETE FROM runtime.supervision_checkpoints']:
            with pytest.raises(DBAPIError), conn.begin_nested():
                conn.execute(text(statement))


def test_checkpoint_ceiling_retains_fallback_required_occurrence_without_grant(graph_env):
    graph = graph_env
    params, paths = admitted(graph, two=True, limit=1)
    with graph.env.engine.begin() as conn:
        first = CheckpointStore.ensure(conn, params, paths[0]).checkpoint
        second = CheckpointStore.ensure(conn, params, paths[1]).checkpoint
        assert first.ordinal == 1 and first.eligibility == 'requestable'
        assert second.ordinal == 2 and second.eligibility == 'fallback_required'
        assert second.reason_code == 'checkpoint_limit_exhausted'
        assert first.seed.decision_id != second.seed.decision_id
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_requests WHERE run_id=:run'), params).scalar_one() == 0


@pytest.mark.parametrize('expired', [False, True])
def test_deadline_is_bounded_by_run_and_expiration_is_explicit(graph_env, expired):
    graph = graph_env
    graph.payload['limits'] = {'deadline_seconds': 1}
    params, paths = admitted(graph)
    if expired:
        time.sleep(1.1)
    with graph.env.engine.begin() as conn:
        deadline = conn.execute(text('SELECT deadline FROM runtime.graph_runs WHERE run_id=:run'), params).scalar_one()
        slot = CheckpointStore.ensure(conn, params, paths[0]).checkpoint
        assert slot.deadline == deadline
        assert slot.reason_code == ('checkpoint_deadline_exhausted' if expired else None)
        assert slot.eligibility == ('fallback_required' if expired else 'requestable')


def test_slot_creation_rollback_and_unready_target_reject(graph_env):
    graph = graph_env
    params, paths = admitted(graph)
    with pytest.raises(RuntimeError, match='rollback-slot'), graph.env.engine.begin() as conn:
        CheckpointStore.ensure(conn, params, paths[0])
        raise RuntimeError('rollback-slot')
    with graph.env.engine.begin() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_checkpoints WHERE run_id=:run'), params).scalar_one() == 0
        conn.execute(text("UPDATE runtime.graph_nodes SET status='issued' WHERE run_id=:run AND kind='invoke'"), params)
        with pytest.raises(ValueError, match='checkpoint_target_not_ready'):
            CheckpointStore.ensure(conn, params, paths[0])


def test_committed_legacy_slot_replays_without_rewriting_as_scalar_profile(graph_env, monkeypatch):
    graph = graph_env
    params, paths = admitted(graph)
    with monkeypatch.context() as legacy:
        legacy.setattr(ValueCheckpointSeed, 'capture',
            lambda policy, footprint, values: CheckpointSeed.capture(policy, footprint))
        with graph.env.engine.begin() as conn:
            original = CheckpointStore.ensure(conn, params, paths[0]).checkpoint
    assert original.seed.document().profile == 'runtime-supervision-checkpoint.v1'
    with graph.env.engine.begin() as conn:
        replay = CheckpointStore.ensure(conn, params, paths[0])
        assert not replay.created and replay.checkpoint == original
        assert not hasattr(replay.checkpoint.seed, 'original_fields_sha256')
