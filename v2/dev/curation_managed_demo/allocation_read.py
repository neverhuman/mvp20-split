"""Planning-only read-only ledger audit; run in independent owner interpreter."""
import importlib.util
import json
import os
import sys
from pathlib import Path

from sqlalchemy import text
from amphora_agent_planning.curation_budget.ceiling import ceiling_for
from amphora_agent_planning.curation_budget.journal import check
from amphora_agent_planning.supervision_api.hosting import serving_engine


def main():
    assert all(importlib.util.find_spec(name) is None for name in (
        'amphora_deployment','amphora_campaign_runtime','amphora_knowledge','amphora_research'))
    source,output=map(Path,sys.argv[1:])
    scope=json.loads(source.read_bytes())
    assert set(scope)=={'tenant_id','project_id'}
    key={'tenant':scope['tenant_id'],'project':scope['project_id']}
    engine=serving_engine(os.environ['ALLOCATION_PLANNING_DATABASE'])
    try:
        with engine.begin() as connection:
            connection.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
            check(connection,key)
            rows=connection.execute(text("SELECT r.engagement_id,r.ordinal,r.accounting_units "
                "FROM planning.reservations r JOIN planning.requests q USING(tenant_id,project_id,engagement_id) "
                "WHERE r.tenant_id=:tenant AND r.project_id=:project "
                "AND convert_from(q.canonical_bytes,'UTF8')::jsonb #>> '{context,model,provider_id}'='openai' "
                "AND convert_from(q.canonical_bytes,'UTF8')::jsonb #>> '{context,output_schema,schema_id}'="
                "'planning.campaign-curation-draft' ORDER BY r.engagement_id,r.ordinal"),key).mappings().all()
        ceiling=ceiling_for(key)
        output.write_text(json.dumps({'status':'passed','scope':scope,
            'original_reservations':[dict(row) for row in rows],
            'reserved_slots':len(rows),'reserved_units':sum(row['accounting_units'] for row in rows),
            'maximum_slots':ceiling.maximum_calls,'maximum_units':ceiling.maximum_units,
            'authorization':ceiling.authorization,'provider_calls':0},indent=2)+'\n')
    finally:engine.dispose()


if __name__=='__main__':main()
