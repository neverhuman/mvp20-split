"""Scope-before-family-before-request locks; existing immutable reservations own spend."""

import json

from sqlalchemy import text

from ..budget.charge import BudgetCharge
from ..budget.policy import BudgetPolicy, ReservationDemand
from ..context.policy import require
from ..providers.wire import observation_document
from .policy import CheckpointAllowance


def lock(connection, key, request):
    if not CheckpointAllowance.applies(request):
        return False
    token = json.dumps(['planning.checkpoint-demo-budget.v1', key['tenant'], key['project']])
    connection.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'), {'token': token})
    return True


def check(connection, key, demand=None):
    """A dedicated project scope is the immutable group; changing worker config cannot reset it."""
    rows = list(connection.execute(text('SELECT r.*,p.canonical_bytes AS policy_bytes, '
        'o.canonical_bytes AS observation_bytes,l.canonical_bytes AS late_bytes '
        'FROM planning.reservations r JOIN planning.budget_policies p '
        'USING(tenant_id,project_id,engagement_id) LEFT JOIN planning.observations o '
        'USING(tenant_id,project_id,engagement_id,ordinal) LEFT JOIN planning.late_observations l '
        'USING(tenant_id,project_id,engagement_id,ordinal) '
        'WHERE r.tenant_id=:tenant AND r.project_id=:project LIMIT 7'), key).mappings())
    ceiling = CheckpointAllowance()
    require(len(rows) + (demand is not None) <= ceiling.maximum_calls, 'checkpoint_group_calls_exhausted')
    units = 0
    for row in rows:
        policy = BudgetPolicy.from_bytes(bytes(row['policy_bytes']))
        require(policy.sha256 == row['policy_sha256'], 'checkpoint_group_policy_digest')
        CheckpointAllowance.validate_policy(policy)
        held = row['accounting_units']
        for field in ('observation_bytes', 'late_bytes'):
            if row[field] is None:
                continue
            wire = observation_document(bytes(row[field]))
            reference = wire.attempt
            require((reference.engagement.scope.tenant_id, reference.engagement.scope.project_id,
                reference.engagement.engagement_id, reference.ordinal) ==
                (row['tenant_id'], row['project_id'], row['engagement_id'], row['ordinal']),
                'checkpoint_group_history')
            original = ReservationDemand(reference, row['policy_sha256'], row['input_tokens'],
                                         row['output_tokens'], row['accounting_units'])
            charge = BudgetCharge.reconcile(original, bytes(row[field]))
            require(not charge.overage, 'provider_usage_overage')
            held = max(held, charge.accounting_units)
        units += held
    require(units + (0 if demand is None else demand.accounting_units) <= ceiling.maximum_units,
            'checkpoint_group_cost_exhausted')
