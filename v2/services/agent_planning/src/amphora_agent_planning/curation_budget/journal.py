"""One fixed configured scope before family/request locks; no reset/refund mechanism."""
import json

from sqlalchemy import text

from ..budget.charge import BudgetCharge
from ..budget.policy import BudgetPolicy, ReservationDemand
from ..context.policy import require
from ..providers.wire import observation_document
from .policy import CurationAllowance
from .ceiling import ceiling_for


def lock(connection, key, request):
    if not CurationAllowance.applies(request):
        return False
    token = json.dumps(['planning.curation-qualification-budget.v1', key['tenant'], key['project']])
    connection.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'), {'token': token})
    return True


def check(connection, key, demand=None):
    ceiling = ceiling_for(key)
    rows = list(connection.execute(text('SELECT r.*,p.canonical_bytes AS policy_bytes, '
        'o.canonical_bytes AS observation_bytes,l.canonical_bytes AS late_bytes '
        'FROM planning.reservations r JOIN planning.budget_policies p '
        'USING(tenant_id,project_id,engagement_id) JOIN planning.requests q '
        'USING(tenant_id,project_id,engagement_id) LEFT JOIN planning.observations o '
        'USING(tenant_id,project_id,engagement_id,ordinal) LEFT JOIN planning.late_observations l '
        'USING(tenant_id,project_id,engagement_id,ordinal) '
        "WHERE r.tenant_id=:tenant AND r.project_id=:project "
        "AND convert_from(q.canonical_bytes,'UTF8')::jsonb #>> '{context,model,provider_id}'='openai' "
        "AND (convert_from(q.canonical_bytes,'UTF8')::jsonb #>> '{context,output_schema,schema_id}'="
        "'planning.campaign-curation-draft' OR convert_from(q.canonical_bytes,'UTF8')::jsonb "
        "#>> '{context,model,tokenizer,schema_id}' IN ('planning.curation-openai-input-bound',"
        "'planning.curation-openai-input-bound.v2','planning.curation-openai-input-bound.v3','planning.curation-openai-input-bound.v4','planning.curation-openai-input-bound.v5','planning.curation-openai-input-bound.v6')) LIMIT :scan_limit"),
        {**key, 'scan_limit': ceiling.maximum_calls + 1}).mappings())
    require(len(rows) + (demand is not None) <= ceiling.maximum_calls, 'curation_group_calls_exhausted')
    units = 0
    for row in rows:
        policy = BudgetPolicy.from_bytes(bytes(row['policy_bytes']))
        require(policy.sha256 == row['policy_sha256'], 'curation_group_policy_digest')
        CurationAllowance.validate_policy(policy)
        held = row['accounting_units']
        for field in ('observation_bytes', 'late_bytes'):
            if row[field] is None:
                continue
            wire = observation_document(bytes(row[field]))
            reference = wire.attempt
            require((reference.engagement.scope.tenant_id, reference.engagement.scope.project_id,
                reference.engagement.engagement_id, reference.ordinal) ==
                (row['tenant_id'], row['project_id'], row['engagement_id'], row['ordinal']),
                'curation_group_history')
            original = ReservationDemand(reference, row['policy_sha256'], row['input_tokens'],
                                         row['output_tokens'], row['accounting_units'])
            charge = BudgetCharge.reconcile(original, bytes(row[field]))
            require(not charge.overage, 'provider_usage_overage')
            held = max(held, charge.accounting_units)
        units += held
    require(units + (0 if demand is None else demand.accounting_units) <= ceiling.maximum_units,
            'curation_group_cost_exhausted')
