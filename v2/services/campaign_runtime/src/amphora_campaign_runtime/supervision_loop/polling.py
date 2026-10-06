"""Disposable fair discovery cursor; durable checkpoint owners retain all authority."""

import time

from amphora_contracts_supervision import SupervisionRef
from sqlalchemy import text

from ..supervision_scope.observations import require

PENDING = '''SELECT s.run_id,s.decision_id FROM runtime.supervision_checkpoints s
 JOIN runtime.supervision_recipes p USING(tenant_id,project_id,run_id)
 WHERE s.tenant_id=:tenant AND s.project_id=:project
 AND NOT EXISTS (SELECT 1 FROM runtime.supervision_winners w
 WHERE w.tenant_id=s.tenant_id AND w.project_id=s.project_id AND w.run_id=s.run_id AND w.decision_id=s.decision_id)
 AND NOT EXISTS (SELECT 1 FROM runtime.supervision_requests r
 WHERE r.tenant_id=s.tenant_id AND r.project_id=s.project_id AND r.run_id=s.run_id
 AND r.decision_id=s.decision_id AND r.prepared_by<>:actor)
 AND (s.run_id,s.decision_id) > (:after_run,:after_decision)
 ORDER BY s.run_id,s.decision_id LIMIT 1'''


class CheckpointPoller:
    def __init__(self, engine, loop):
        self.engine, self.loop = engine, loop
        self.cursors = {}

    def tick(self, principal):
        for action in ('read', 'supervise_prepare', 'supervise_dispatch', 'supervise_accept'):
            principal.require(action)
        key = (principal.scope.tenant_id, principal.scope.project_id, principal.actor_id)
        after = self.cursors.get(key, ('', ''))
        params = {'tenant': key[0], 'project': key[1], 'actor': key[2],
                  'after_run': after[0], 'after_decision': after[1]}
        with self.engine.connect() as conn:
            row = conn.execute(text(PENDING), params).one_or_none()
            if row is None and after != ('', ''):
                row = conn.execute(text(PENDING), {**params, 'after_run': '', 'after_decision': ''}).one_or_none()
        if row is None:
            self.cursors.pop(key, None)
            return None
        self.cursors[key] = (row.run_id, row.decision_id)
        reference = SupervisionRef(scope=principal.scope, run_id=row.run_id, decision_id=row.decision_id)
        return self.loop.tick(principal, reference)

    def sweep(self, principal, *, seconds=20, interval=1):
        require(type(seconds) in (int, float) and 0 < seconds <= 86400 and
                type(interval) in (int, float) and 0.05 <= interval <= 60, 'checkpoint_polling_window')
        deadline, counts = time.monotonic() + seconds, {}
        while time.monotonic() < deadline:
            result = self.tick(principal)
            stage = 'idle' if result is None else result.stage
            counts[stage] = counts.get(stage, 0) + 1
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(interval, remaining))
        return counts
