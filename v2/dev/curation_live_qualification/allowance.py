"""Planning-owned, read-only allowance report; run solely in its installed interpreter."""
import importlib.util
import json
import sys
from pathlib import Path

from sqlalchemy import text
from amphora_agent_planning.curation_budget.journal import check
from amphora_agent_planning.curation_budget.policy import CurationAllowance
from amphora_agent_planning.curation_worker.hosting import CurationHost


def main():
    assert all(importlib.util.find_spec(name) is None for name in (
        'amphora_campaign_runtime', 'amphora_data_artifacts', 'amphora_deployment',
        'amphora_research', 'amphora_knowledge', 'amphora_capability_registry'))
    config, output = map(Path, sys.argv[1:])
    host = CurationHost.load(config)  # Provider disabled; no key read.
    try:
        scope = host.principal.scope
        host.principal.require('read_attempts', scope)
        key = {'tenant': scope.tenant_id, 'project': scope.project_id}
        with host.engine.begin() as connection:
            connection.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
            check(connection, key)
            rows = connection.execute(text('SELECT r.engagement_id,r.ordinal,r.accounting_units '
                'FROM planning.reservations r JOIN planning.requests q '
                'USING(tenant_id,project_id,engagement_id) '
                'WHERE r.tenant_id=:tenant AND r.project_id=:project '
                "AND convert_from(q.canonical_bytes,'UTF8')::jsonb #>> '{context,model,provider_id}'='openai' "
                "AND (convert_from(q.canonical_bytes,'UTF8')::jsonb #>> '{context,output_schema,schema_id}'="
                "'planning.campaign-curation-draft' OR convert_from(q.canonical_bytes,'UTF8')::jsonb "
                "#>> '{context,model,tokenizer,schema_id}'='planning.curation-openai-input-bound') "
                'ORDER BY r.engagement_id,r.ordinal LIMIT 5'), key).mappings().all()
        held = sum(row['accounting_units'] for row in rows)
        value = {'scope': scope.model_dump(mode='json'), 'canonical_check': 'passed',
            'original_reservations': [dict(row) for row in rows], 'reserved_slots': len(rows),
            'reserved_units': held, 'maximum_slots': CurationAllowance.maximum_calls,
            'maximum_units': CurationAllowance.maximum_units,
            'remaining_slots': CurationAllowance.maximum_calls - len(rows),
            'remaining_reservation_units': CurationAllowance.maximum_units - held,
            'unit': 'usd_nanodollars', 'provider_enabled': False}
        output.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    finally:
        host.close()


if __name__ == '__main__':
    main()
