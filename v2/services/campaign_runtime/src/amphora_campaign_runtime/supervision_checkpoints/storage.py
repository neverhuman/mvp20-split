"""Run-serialized create-once slots; no request dispatch or winner application."""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from amphora_contracts_campaigns import parse_execution_plan
from amphora_contracts_graph_runtime import GraphReadCut
from sqlalchemy import text

from ..compiler.addresses import ActivationAddress
from ..coordinator.storage import GraphStorage
from ..graph_inspection.policy import node_view
from ..lifecycle.claims import RUN
from ..supervision_journal.current import verify_footprint
from ..supervision_policy.storage import PolicyPins
from ..supervision_scope import NodeObservation
from ..supervision_scope.checkpoints import CheckpointFootprint, CheckpointTarget
from ..supervision_scope.observations import require
from .seed import CheckpointSeed


@dataclass(frozen=True)
class StoredCheckpoint:
    seed: CheckpointSeed
    ordinal: int
    eligibility: str
    reason_code: str | None
    created_at: datetime
    deadline: datetime

    @classmethod
    def from_row(cls, row, policy):
        seed = CheckpointSeed(bytes(row['canonical_seed']), policy)
        record = seed.document()
        cut = record.snapshot.cut
        expected = {'tenant_id': cut.scope.tenant_id, 'project_id': cut.scope.project_id,
            'run_id': cut.run_id, 'activation_id': record.snapshot.checkpoints[0].activation_id,
            'decision_id': seed.decision_id, 'policy_sha256': policy.sha256,
            'checkpoint_id': record.checkpoint_id, 'seed_sha256': seed.sha256}
        require(all(row[key] == value for key, value in expected.items()), 'stored_checkpoint_identity')
        rule = next(rule for rule in policy.document().checkpoints if rule.checkpoint_id == record.checkpoint_id)
        require(1 <= row['ordinal'] <= 100000 and row['deadline'] <= row['created_at'] + timedelta(seconds=rule.timeout_seconds),
                'stored_checkpoint_limits')
        reason = ('checkpoint_deadline_exhausted' if row['deadline'] <= row['created_at'] else
                  'checkpoint_limit_exhausted' if row['ordinal'] > policy.document().ceilings.max_checkpoints else None)
        require(row['reason_code'] == reason and
                row['eligibility'] == ('fallback_required' if reason else 'requestable'), 'stored_checkpoint_eligibility')
        return cls(seed, row['ordinal'], row['eligibility'], reason, row['created_at'], row['deadline'])


@dataclass(frozen=True)
class OpenedCheckpoint:
    checkpoint: StoredCheckpoint
    created: bool


class CheckpointStore:
    @staticmethod
    def ensure(conn, params, path):
        run = conn.execute(text('SELECT * FROM runtime.runs WHERE ' + RUN + ' FOR UPDATE'), params).mappings().one()
        graph = GraphStorage.graph(conn, params)
        document = conn.execute(text('SELECT document FROM runtime.graph_plans WHERE tenant_id=:tenant '
            'AND project_id=:project AND plan_sha256=:plan'), {**params, 'plan': graph['plan_sha256']}).scalar_one()
        plan = parse_execution_plan(json.dumps(document))
        policy = PolicyPins.load(conn, params, plan)
        require(policy is not None, 'supervised_run_required')
        rule = policy.rule_for(path)
        require(rule is not None, 'checkpoint_rule_missing')
        activation = ActivationAddress.for_plan(plan, path).key
        binding = {**params, 'activation': activation}
        previous = conn.execute(text('SELECT * FROM runtime.supervision_checkpoints WHERE ' + RUN +
            ' AND activation_id=:activation'), binding).mappings().one_or_none()
        if previous is not None:
            require(previous['deadline'] <= graph['deadline'], 'stored_checkpoint_run_deadline')
            return OpenedCheckpoint(StoredCheckpoint.from_row(previous, policy), False)
        require(run['status'] == 'running', 'run_not_running')
        ids = [ActivationAddress.for_plan(plan, item).key for item in policy.read_paths(path)]
        rows = conn.execute(text('SELECT * FROM runtime.graph_nodes WHERE ' + RUN + ' AND activation_id=ANY(:ids)'),
                            {**params, 'ids': ids}).mappings().all()
        observations = tuple(NodeObservation.capture(plan.sha256, node_view(row), state=row['state'], outputs=row['outputs'])
                             for row in rows)
        target = next((item for item in observations if item.identity == activation), None)
        require(target is not None and target.view.status == 'ready', 'checkpoint_target_not_ready')
        cut = GraphReadCut(scope=policy.document().scope, run_id=params['run'], plan_sha256=plan.sha256,
                           revision=run['revision'], frontier_revision=graph['frontier_revision'])
        footprint = CheckpointFootprint(cut, (CheckpointTarget(activation, rule.kind,
            tuple(field.name for field in rule.fields)),), observations)
        seed = CheckpointSeed.capture(policy, footprint)
        verify_footprint(conn, params, run, footprint)
        ordinal = conn.execute(text('SELECT count(*)+1 FROM runtime.supervision_checkpoints WHERE ' + RUN), params).scalar_one()
        require(ordinal <= graph['max_activations'], 'checkpoint_activation_limit')
        created = conn.execute(text('SELECT clock_timestamp()')).scalar_one()
        deadline = min(graph['deadline'], created + timedelta(seconds=rule.timeout_seconds))
        reason = ('checkpoint_deadline_exhausted' if deadline <= created else
                  'checkpoint_limit_exhausted' if ordinal > policy.document().ceilings.max_checkpoints else None)
        values = {**binding, 'decision': seed.decision_id, 'policy': policy.sha256, 'checkpoint': rule.checkpoint_id,
            'ordinal': ordinal, 'digest': seed.sha256, 'canonical': seed.canonical,
            'eligibility': 'fallback_required' if reason else 'requestable', 'reason': reason,
            'created': created, 'deadline': deadline}
        row = conn.execute(text('INSERT INTO runtime.supervision_checkpoints '
            '(tenant_id,project_id,run_id,activation_id,decision_id,policy_sha256,checkpoint_id,ordinal,seed_sha256,'
            'canonical_seed,eligibility,reason_code,created_at,deadline) VALUES '
            '(:tenant,:project,:run,:activation,:decision,:policy,:checkpoint,:ordinal,:digest,:canonical,'
            ':eligibility,:reason,:created,:deadline) RETURNING *'), values).mappings().one()
        return OpenedCheckpoint(StoredCheckpoint.from_row(row, policy), True)
