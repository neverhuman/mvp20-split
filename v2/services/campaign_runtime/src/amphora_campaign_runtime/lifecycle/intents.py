"""Irrevocable abort tombstones owned by runtime authority transitions."""

import json
from dataclasses import dataclass

from sqlalchemy import text


@dataclass(frozen=True, slots=True)
class AbortDecision:
    runtime_receipt_id: str
    reason_code: str

    def record(self):
        return {"status": "aborted", "runtime_receipt_id": self.runtime_receipt_id, "reason_code": self.reason_code}

    def apply(self, conn, params, worker_id=None):
        # Caller locks run, activation and attempt before these intent locks.
        where = "i.tenant_id=:tenant AND i.project_id=:project AND i.run_id=:run AND i.status='prepared'"
        if worker_id is not None:
            where += " AND a.worker_id=:worker"
        values = {**params, "worker": worker_id, "proof": json.dumps(self.record())}
        ids = conn.execute(text("SELECT i.intent_id FROM runtime.completion_intents i JOIN runtime.attempts a "
            "USING (tenant_id,project_id,run_id,activation_id,attempt_id,fence) WHERE " + where +
            " ORDER BY i.intent_id FOR UPDATE OF i"), values).scalars().all()
        for intent in ids:
            conn.execute(text("UPDATE runtime.completion_intents SET status='aborted',outcome=CAST(:proof AS jsonb) "
                "WHERE tenant_id=:tenant AND project_id=:project AND intent_id=:intent AND status='prepared'"),
                {**values, "intent": intent})
        return tuple(ids)
