"""Owned SQL hints select bounded work; workers revalidate every original record."""

from sqlalchemy import text

CHECKPOINT = '''EXISTS (SELECT 1 FROM planning.supervision_commands c
 WHERE c.tenant_id=r.tenant_id AND c.project_id=r.project_id AND c.actor_id=r.actor_id
 AND c.committed_engagement_id=r.engagement_id AND c.family='planning.supervision.request.v2')'''

EXECUTION = '''SELECT r.engagement_id FROM planning.supervision_requests r
 WHERE r.tenant_id=:tenant AND r.project_id=:project AND r.actor_id=:actor AND ''' + CHECKPOINT + '''
 AND NOT EXISTS (SELECT 1 FROM planning.checkpoint_execution_reports x
 WHERE x.tenant_id=r.tenant_id AND x.project_id=r.project_id AND x.engagement_id=r.engagement_id)
 AND r.engagement_id > :after_engagement ORDER BY r.engagement_id LIMIT 1'''

CAPTURE = '''WITH observations AS (
 SELECT tenant_id,project_id,engagement_id,ordinal,'primary' AS kind FROM planning.observations
 UNION ALL SELECT tenant_id,project_id,engagement_id,ordinal,'late' AS kind FROM planning.late_observations)
 SELECT r.engagement_id,o.ordinal,o.kind FROM observations o
 JOIN planning.supervision_requests r ON r.tenant_id=o.tenant_id AND r.project_id=o.project_id
 AND r.engagement_id=o.engagement_id
 JOIN planning.settlements s ON s.tenant_id=o.tenant_id AND s.project_id=o.project_id
 AND s.engagement_id=o.engagement_id AND s.ordinal=o.ordinal
 JOIN planning.campaign_preparations p ON p.tenant_id=o.tenant_id AND p.project_id=o.project_id
 AND p.engagement_id=o.engagement_id
 LEFT JOIN planning.capture_publications u ON u.tenant_id=r.tenant_id AND u.project_id=r.project_id
 AND u.engagement_id=r.engagement_id AND u.ordinal=o.ordinal AND u.observation_kind=o.kind
 WHERE r.tenant_id=:tenant AND r.project_id=:project AND r.actor_id=:actor AND ''' + CHECKPOINT + '''
 AND NOT EXISTS (SELECT 1 FROM planning.capture_response_observations x
 WHERE x.tenant_id=u.tenant_id AND x.project_id=u.project_id AND x.publication_id=u.publication_id
 AND ((convert_from(x.receipt_bytes,'UTF8')::jsonb->'outcome'->>'status')='rejected'
 OR ((convert_from(x.receipt_bytes,'UTF8')::jsonb->'outcome'->>'status')='recorded' AND x.readback_bytes IS NOT NULL)))
 AND NOT EXISTS (SELECT 1 FROM planning.capture_publication_events e
 WHERE e.tenant_id=u.tenant_id AND e.project_id=u.project_id AND e.publication_id=u.publication_id
 AND (convert_from(e.canonical_bytes,'UTF8')::jsonb->>'action')='rejected')
 AND (r.engagement_id,o.ordinal,o.kind) > (:after_engagement,:after_ordinal,:after_kind)
 ORDER BY r.engagement_id,o.ordinal,o.kind LIMIT 1'''


class WorkDiscovery:
    def __init__(self, engine):
        self.engine, self.cursors = engine, {}

    def next(self, principal, lane):
        key = (principal.scope.tenant_id, principal.scope.project_id, principal.actor_id, lane)
        initial = ('', 0, '')
        after = self.cursors.get(key, initial)
        params = {'tenant': key[0], 'project': key[1], 'actor': key[2]}
        query = text(EXECUTION if lane == 'execution' else CAPTURE)
        def fetch(conn, position):
            return conn.execute(query, {**params, 'after_engagement': position[0],
                'after_ordinal': position[1], 'after_kind': position[2]}).one_or_none()
        with self.engine.connect() as conn:
            row = fetch(conn, after)
            if row is None and after != initial:
                row = fetch(conn, initial)
        if row is None:
            self.cursors.pop(key, None)
            return None
        self.cursors[key] = (row.engagement_id, 0, '') if lane == 'execution' else tuple(row)
        return row
