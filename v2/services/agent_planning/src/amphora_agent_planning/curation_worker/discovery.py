"""Own-state keyset discovery is a hint; claim revalidates original authority."""
from sqlalchemy import text
from amphora_contracts_core import Identifier
from pydantic import TypeAdapter
from ..context.policy import require

QUERY = """SELECT r.curation_id FROM planning.curation_requests r
 LEFT JOIN LATERAL (SELECT convert_from(p.view_bytes,'UTF8')::jsonb AS view
 FROM planning.curation_progress p WHERE p.tenant_id=r.tenant_id AND p.project_id=r.project_id
 AND p.curation_id=r.curation_id ORDER BY p.revision DESC LIMIT 1) progress ON true
 WHERE r.tenant_id=:tenant AND r.project_id=:project AND r.actor_id=:actor
 AND convert_from(r.command_bytes,'UTF8')::jsonb #>> '{payload,policy_id}' = ANY(:policies)
 AND COALESCE(progress.view #>> '{receipt,phase}', 'queued') NOT IN ('ready','failed','indeterminate','abstained')
 AND NOT (COALESCE(progress.view #>> '{receipt,phase}', 'queued')='proposed'
 AND COALESCE(progress.view #>> '{proposal,outcome,kind}', '')='request_capabilities')
 AND NOT EXISTS (SELECT 1 FROM planning.curation_leases l WHERE l.tenant_id=r.tenant_id
 AND l.project_id=r.project_id AND l.curation_id=r.curation_id AND l.lease_until>clock_timestamp())
 AND r.curation_id>:after ORDER BY r.curation_id LIMIT 1"""


class CurationDiscovery:
    def __init__(self, engine, policies):
        require(type(policies) in (tuple, list) and 1 <= len(policies) <= 32, 'curation_worker_policy_count')
        values = tuple(TypeAdapter(Identifier).validate_python(value, strict=True) for value in policies)
        require(len(set(values)) == len(values), 'curation_worker_policy_duplicate')
        self.engine, self.policies, self.cursors = engine, values, {}

    def next(self, principal):
        principal.require('execute_curations', principal.scope)
        key = (principal.scope.tenant_id, principal.scope.project_id, principal.actor_id)
        params = dict(tenant=key[0], project=key[1], actor=key[2], policies=list(self.policies))
        after = self.cursors.get(key, '')
        with self.engine.connect() as conn:
            result = conn.execute(text(QUERY), {**params, 'after': after}).scalar_one_or_none()
            if result is None and after:
                result = conn.execute(text(QUERY), {**params, 'after': ''}).scalar_one_or_none()
        self.cursors[key] = result or ''
        return result
