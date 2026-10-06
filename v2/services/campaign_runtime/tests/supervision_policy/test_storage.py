"""Actual PostgreSQL pin identity, transaction rollback and immutable service grants."""

import json
import uuid
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.coordinator import ReviewedPlan
from amphora_campaign_runtime.coordinator.frontier import FrontierPlanner, ScopeAddress
from amphora_campaign_runtime.coordinator.storage import GraphStorage
from amphora_campaign_runtime.coordinator.values import BoundValues
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.persistence.commands import CommandStore
from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.storage import PolicyPins
from amphora_contracts_supervision import parse_supervised_admission
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .support import plan, policy


@pytest.fixture
def pinned_env(fixture_env):
    env = fixture_env
    graph = plan(scope=env.principal.scope.model_dump(mode='json'))
    reviewed = ReviewedPolicy.bind(graph, policy(graph))
    command = parse_supervised_admission(json.dumps({'encoding': 'amphora-command-v2', 'identity': {
        'scope': env.principal.scope.model_dump(mode='json'), 'actor_id': env.principal.actor_id,
        'command_family': 'graph.admit_supervised', 'command_id': uuid.uuid4().hex},
        'payload': {'admission': {'plan_sha256': graph.sha256, 'inputs': [], 'budget': {'limit': 2}},
                    'policy_sha256': reviewed.sha256}}))
    CommandStore(env.engine).register(command)
    params = {'tenant': env.principal.scope.tenant_id, 'project': env.principal.scope.project_id,
              'run': uuid.uuid4().hex, 'digest': graph.sha256}

    def seed(conn):
        GraphStorage.retain_plan(conn, params, ReviewedPlan(graph, ()))
        conn.execute(text("INSERT INTO runtime.runs (tenant_id,project_id,run_id,fixture_id,plan_sha256,"
            "input_snapshot,status,budget_limit,execution_mode) VALUES (:tenant,:project,:run,'fixture',:digest,"
            "'{}','running',2,'graph')"), params)
        conn.execute(text('INSERT INTO runtime.graph_runs (tenant_id,project_id,run_id,plan_sha256,inputs,'
            "max_activations,deadline) VALUES (:tenant,:project,:run,:digest,'[]',100,clock_timestamp()+interval '1 minute')"), params)

    return SimpleNamespace(env=env, graph=graph, policy=reviewed, command=command, params=params, seed=seed)


def test_exact_pin_survives_connection_replacement_and_is_append_only(pinned_env):
    e = pinned_env
    with e.env.engine.begin() as conn:
        e.seed(conn)
        assert PolicyPins.load(conn, e.params, e.graph) is None
        PolicyPins.pin(conn, e.params['run'], e.command, e.policy)
    with e.env.engine.begin() as conn:
        assert PolicyPins.load(conn, e.params, e.graph) == e.policy
        for statement in ['UPDATE runtime.supervision_policies SET policy_sha256=policy_sha256',
                          'DELETE FROM runtime.supervision_policies']:
            with pytest.raises(DBAPIError), conn.begin_nested():
                conn.execute(text(statement))
        with pytest.raises(DBAPIError), conn.begin_nested():
            PolicyPins.pin(conn, e.params['run'], e.command, e.policy)


def test_aborted_admission_leaves_no_run_or_policy_pin(pinned_env):
    e = pinned_env
    with pytest.raises(RuntimeError, match='admission-abort'), e.env.engine.begin() as conn:
        e.seed(conn)
        PolicyPins.pin(conn, e.params['run'], e.command, e.policy)
        raise RuntimeError('admission-abort')
    with e.env.engine.connect() as conn:
        assert PolicyPins.load(conn, e.params, e.graph) is None
        assert conn.execute(text('SELECT count(*) FROM runtime.runs WHERE run_id=:run'), e.params).scalar_one() == 0


def test_existing_frontier_prevents_policy_retrofit(pinned_env):
    e = pinned_env
    with e.env.engine.begin() as conn:
        e.seed(conn)
        address = ScopeAddress(e.graph.sha256)
        GraphStorage.create_scope(conn, e.params, address, BoundValues(()), FrontierPlanner().scope(e.graph, address))
        with pytest.raises(TransitionError, match='supervision_pin_after_admission'):
            PolicyPins.pin(conn, e.params['run'], e.command, e.policy)
        assert PolicyPins.load(conn, e.params, e.graph) is None


def test_policy_cannot_differ_from_registered_command(pinned_env):
    e = pinned_env
    data = e.policy.document().model_dump(mode='json')
    data['checkpoints'][0]['fallback'] = 'block_target'
    changed = ReviewedPolicy.bind(e.graph, type(e.policy.document()).model_validate_json(json.dumps(data)))
    with e.env.engine.begin() as conn:
        e.seed(conn)
        with pytest.raises(TransitionError, match='supervision_policy_binding'):
            PolicyPins.pin(conn, e.params['run'], e.command, changed)
        assert PolicyPins.load(conn, e.params, e.graph) is None


def test_changed_pending_command_cannot_pin(pinned_env):
    e = pinned_env
    data = json.loads(e.command.canonical_bytes)
    data['payload']['admission']['budget']['limit'] = 3
    changed = parse_supervised_admission(json.dumps(data))
    with e.env.engine.begin() as conn:
        e.seed(conn)
        with pytest.raises(TransitionError, match='supervision_admission_command_mismatch'):
            PolicyPins.pin(conn, e.params['run'], changed, e.policy)
        assert PolicyPins.load(conn, e.params, e.graph) is None


def test_corrupt_stored_identity_is_not_reconstructed_as_a_valid_pin(pinned_env):
    e = pinned_env
    with e.env.engine.begin() as conn:
        e.seed(conn)
        conn.execute(text('INSERT INTO runtime.supervision_policies '
            '(tenant_id,project_id,run_id,plan_sha256,policy_sha256,canonical_policy,actor_id,family,command_id) '
            "VALUES (:tenant,:project,:run,:digest,:wrong,:canonical,:actor,'graph.admit_supervised',:command)"),
            {**e.params, 'wrong': 'f' * 64, 'canonical': e.policy.canonical,
             'actor': e.command.identity.actor_id, 'command': e.command.identity.command_id})
        with pytest.raises(TransitionError, match='stored_supervision_policy_mismatch'):
            PolicyPins.load(conn, e.params, e.graph)
