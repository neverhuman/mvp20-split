"""Transaction-local immutable admission pins; no network or independent transaction."""

import json

from amphora_contracts_campaigns import parse_execution_plan
from amphora_contracts_supervision import (
    AdmitSupervisedGraph,
    parse_supervised_admission,
)
from sqlalchemy import text

from ..lifecycle.claims import RUN
from ..lifecycle.model import TransitionError
from ..persistence.commands import WHERE, _bindings
from .policy import ReviewedPolicy


def ensure(condition, code):
    if not condition:
        raise TransitionError(code)


class PolicyPins:
    @staticmethod
    def pin(conn, run_id, command, policy):
        command = parse_supervised_admission(command.canonical_bytes)
        request = AdmitSupervisedGraph.model_validate_json(json.dumps(json.loads(command.canonical_bytes)['payload']))
        record = policy.document()
        ensure(record.scope == command.identity.scope and record.plan_sha256 == request.admission.plan_sha256 and
               policy.sha256 == request.policy_sha256, 'supervision_policy_binding')
        params = {**_bindings(command), 'run': run_id}
        run = conn.execute(text('SELECT status,revision FROM runtime.runs WHERE ' + RUN + ' FOR UPDATE'), params).mappings().one()
        ensure(run['status'] == 'running' and run['revision'] == 0, 'supervision_pin_after_admission')
        ensure(not conn.execute(text('SELECT EXISTS(SELECT 1 FROM runtime.graph_scopes WHERE ' + RUN + ')'), params).scalar_one(),
               'supervision_pin_after_admission')
        original = conn.execute(text('SELECT status,canonical_bytes FROM runtime.commands WHERE ' + WHERE), params).mappings().one()
        ensure(original['status'] == 'pending' and bytes(original['canonical_bytes']) == command.canonical_bytes,
               'supervision_admission_command_mismatch')
        document = conn.execute(text('SELECT p.document FROM runtime.graph_runs g JOIN runtime.graph_plans p '
            'USING (tenant_id,project_id,plan_sha256) WHERE g.tenant_id=:tenant AND g.project_id=:project AND g.run_id=:run'),
            params).scalar_one()
        reviewed = ReviewedPolicy.from_bytes(parse_execution_plan(json.dumps(document)), policy.canonical)
        conn.execute(text('INSERT INTO runtime.supervision_policies '
            '(tenant_id,project_id,run_id,plan_sha256,policy_sha256,canonical_policy,actor_id,family,command_id) '
            'VALUES (:tenant,:project,:run,:plan,:policy,:canonical,:actor,:family,:command)'),
            {**params, 'plan': record.plan_sha256, 'policy': reviewed.sha256, 'canonical': reviewed.canonical})

    @staticmethod
    def load(conn, params, plan):
        row = conn.execute(text('SELECT plan_sha256,policy_sha256,canonical_policy FROM runtime.supervision_policies '
            'WHERE ' + RUN), params).mappings().one_or_none()
        if row is None:
            return None
        policy = ReviewedPolicy.from_bytes(plan, bytes(row['canonical_policy']))
        ensure(row['plan_sha256'] == plan.sha256 and row['policy_sha256'] == policy.sha256,
               'stored_supervision_policy_mismatch')
        scope = policy.document().scope
        ensure(scope.tenant_id == params['tenant'] and scope.project_id == params['project'],
               'stored_supervision_policy_scope')
        return policy
