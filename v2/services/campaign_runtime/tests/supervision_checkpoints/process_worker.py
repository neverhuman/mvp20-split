"""Installed Runtime transaction barriers; database credentials stay in environment."""

import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.storage import GraphStorage
from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.supervision_checkpoints.storage import (
    CheckpointStore,
    StoredCheckpoint,
)
from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.catalog import PolicyCatalog
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import parse_graph_command
from amphora_contracts_runtime import parse_command
from amphora_contracts_supervision import parse_supervised_admission
from sqlalchemy import create_engine, text

from ..supervision_policy.support import plan, policy

STATE = Path(os.environ['AMPHORA_CHECKPOINT_STATE'])
OUTPUT = Path(os.environ['AMPHORA_CHECKPOINT_OUTPUT'])
MODE = os.environ['AMPHORA_CHECKPOINT_MODE']


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def encoded(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def barrier():
    gate = os.environ.get('AMPHORA_CHECKPOINT_GATE')
    if gate:
        Path(str(OUTPUT) + '.ready').write_text('ready', encoding='utf-8')
        deadline = time.monotonic() + 45
        while not Path(gate).exists():
            assert time.monotonic() < deadline, 'barrier timeout'
            time.sleep(0.02)


def snapshot(conn, params, admitted_policy):
    row = conn.execute(text('SELECT * FROM runtime.supervision_checkpoints WHERE run_id=:run'), params).mappings().one()
    slot = StoredCheckpoint.from_row(row, admitted_policy)
    assert slot.seed.document().original_fields[0].value.value == 1
    assert conn.execute(text('SELECT count(*) FROM runtime.binding_intents WHERE run_id=:run'), params).scalar_one() == 0
    assert conn.execute(text('SELECT count(*) FROM runtime.activations WHERE run_id=:run'), params).scalar_one() == 0
    return {'decision_id': slot.seed.decision_id, 'seed_sha256': slot.seed.sha256,
        'original_fields_sha256': slot.seed.original_fields_sha256, 'created_at': slot.created_at.isoformat(),
        'deadline': slot.deadline.isoformat(), 'ordinal': slot.ordinal, 'eligibility': slot.eligibility}


def test_process_stage(monkeypatch):
    assert importlib.metadata.version('amphora-campaign-runtime') == '0.40.0'
    import amphora_campaign_runtime
    assert Path(amphora_campaign_runtime.__file__).absolute().is_relative_to(Path(sys.prefix).absolute())
    assert all(importlib.util.find_spec(name) is None for name in (
        'amphora_agent_planning', 'amphora_data_artifacts', 'amphora_research', 'amphora_knowledge', 'amphora_capability_registry'))
    Path(str(OUTPUT) + '.pid').write_text(str(os.getpid()), encoding='utf-8')
    metadata = json.loads(STATE.read_bytes())
    scope = Scope.model_validate_json(json.dumps(metadata['scope']))
    graph = plan(nested=True, scope=metadata['scope'])
    admitted_policy = ReviewedPolicy.bind(graph, policy(graph, nested=True))
    principal = RuntimePrincipal('checkpoint-owner', scope, frozenset({'admit', 'maintain', 'read', 'cancel'}))
    engine = create_engine(os.environ['AMPHORA_CHECKPOINT_SQL_URL'], connect_args={'options': '-c statement_timeout=15000'})
    admission = GraphAdmission(engine, PlanCatalog([ReviewedPlan(graph, ())]), bindings_enabled=True,
                               policies=PolicyCatalog([admitted_policy]))
    params = {'tenant': scope.tenant_id, 'project': scope.project_id, 'run': metadata.get('run')}

    def command(family, payload, key):
        return json.dumps({'identity': {'scope': metadata['scope'], 'actor_id': principal.actor_id,
            'command_family': family, 'command_id': key}, 'payload': payload})

    try:
        if MODE == 'initialize':
            raw = json.loads(command('graph.admit_supervised', {'admission': {
                'plan_sha256': graph.sha256, 'inputs': [], 'budget': {'limit': 2}},
                'policy_sha256': admitted_policy.sha256}, 'admit-checkpoint'))
            raw['encoding'] = 'amphora-command-v2'
            original = parse_supervised_admission(json.dumps(raw))
            metadata['admission'] = base64.b64encode(original.canonical_bytes).decode()
            write(STATE, metadata)
            write(OUTPUT, {'mode': MODE, 'plan_sha256': graph.sha256, 'policy_sha256': admitted_policy.sha256,
                           'command_sha256': original.sha256})
            return
        if MODE == 'cleanup':
            with engine.connect() as conn:
                runs = conn.execute(text("SELECT run_id FROM runtime.runs WHERE tenant_id=:tenant AND project_id=:project AND status='running'"), params).scalars().all()
            for run_id in runs:
                receipt = AuthorityCommands(engine).cancel(principal, parse_command('runtime.cancel',
                    command('runtime.cancel', {'run_id': run_id, 'reason_code': 'checkpoint_probe_cleanup'}, 'cleanup-' + run_id)))
                assert receipt.outcome.status == 'accepted'
            write(OUTPUT, {'mode': MODE, 'scoped_cleanup': True, 'cancelled_runs': len(runs)})
            return
        original = parse_supervised_admission(base64.b64decode(metadata['admission']))
        barrier()
        if MODE == 'kill_admission':
            create = GraphStorage.create_scope

            def killed(*args, **kwargs):
                create(*args, **kwargs)
                write(OUTPUT, {'mode': MODE, 'barrier': 'policy_and_frontier_before_commit'})
                os._exit(91)

            monkeypatch.setattr(GraphStorage, 'create_scope', killed)
            admission.admit_supervised(principal, original)
            raise AssertionError('admission barrier missing')
        if MODE == 'inspect_admission_rollback':
            with engine.connect() as conn:
                for table in ('runs', 'graph_plans', 'supervision_policies', 'graph_scopes', 'graph_nodes', 'supervision_checkpoints'):
                    assert conn.execute(text(f'SELECT count(*) FROM runtime.{table} WHERE tenant_id=:tenant AND project_id=:project'), params).scalar_one() == 0
                status = conn.execute(text("SELECT status FROM runtime.commands WHERE tenant_id=:tenant AND project_id=:project AND family='graph.admit_supervised'"), params).scalar_one()
                assert status == 'pending'
            write(OUTPUT, {'mode': MODE, 'pending_command': True, 'no_partial_admission': True})
            return
        if MODE in {'admit', 'replay_admission'}:
            if MODE == 'replay_admission':
                admission = GraphAdmission(engine, PlanCatalog([]), policies=PolicyCatalog([]))
            receipt = admission.admit_supervised(principal, original)
            assert receipt.outcome.status == 'accepted'
            write(OUTPUT, {'run': receipt.outcome.committed.object_id, 'receipt': receipt.model_dump(mode='json'),
                           'receipt_sha256': encoded(receipt.model_dump(mode='json'))})
            return
        advance = parse_graph_command('graph.advance', command('graph.advance', {'run_id': metadata['run']}, 'advance-checkpoint'))
        if MODE == 'kill_advance':
            ensure = CheckpointStore.ensure

            def killed(*args, **kwargs):
                result = ensure(*args, **kwargs)
                assert result.created
                write(OUTPUT, {'mode': MODE, 'barrier': 'checkpoint_before_advance_commit',
                               'uncommitted_seed': result.checkpoint.seed.sha256})
                os._exit(92)

            monkeypatch.setattr(CheckpointStore, 'ensure', killed)
            GraphAdvancer(engine).advance(principal, advance)
            raise AssertionError('advance barrier missing')
        if MODE == 'inspect_advance_rollback':
            with engine.connect() as conn:
                assert conn.execute(text('SELECT count(*) FROM runtime.supervision_checkpoints WHERE run_id=:run'), params).scalar_one() == 0
                assert conn.execute(text('SELECT count(*) FROM runtime.graph_scopes WHERE run_id=:run'), params).scalar_one() == 1
                assert conn.execute(text("SELECT status FROM runtime.graph_nodes WHERE run_id=:run AND node_id='loop'"), params).scalar_one() == 'ready'
                assert conn.execute(text("SELECT status FROM runtime.commands WHERE tenant_id=:tenant AND project_id=:project AND family='graph.advance'"), params).scalar_one() == 'pending'
            write(OUTPUT, {'mode': MODE, 'no_partial_expansion_or_slot': True, 'pending_command': True})
            return
        if MODE in {'advance', 'fresh_advance', 'terminal_replay'}:
            if MODE == 'fresh_advance':
                advance = parse_graph_command('graph.advance', command('graph.advance', {'run_id': metadata['run']}, 'advance-fresh'))
            receipt = GraphAdvancer(engine).advance(principal, advance)
            assert receipt.outcome.status == 'accepted'
            with engine.connect() as conn:
                evidence = snapshot(conn, params, admitted_policy)
            write(OUTPUT, {'receipt': receipt.model_dump(mode='json'), 'checkpoint': evidence})
            return
        if MODE == 'cancel':
            receipt = AuthorityCommands(engine).cancel(principal, parse_command('runtime.cancel',
                command('runtime.cancel', {'run_id': metadata['run'], 'reason_code': 'checkpoint_probe_complete'}, 'cancel-checkpoint')))
            assert receipt.outcome.status == 'accepted'
            with engine.connect() as conn:
                assert conn.execute(text('SELECT status FROM runtime.runs WHERE run_id=:run'), params).scalar_one() == 'cancelled'
            write(OUTPUT, {'mode': MODE, 'run_cancelled': True})
            return
        raise AssertionError('unknown probe mode')
    finally:
        engine.dispose()
