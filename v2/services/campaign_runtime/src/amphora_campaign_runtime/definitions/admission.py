"""Draft-specific guards within the existing Runtime admission authority."""

import json
import uuid
from dataclasses import dataclass
from types import MappingProxyType

from sqlalchemy import text

from ..coordinator.values import ensure
from . import storage
from .material import ValidationMaterial


@dataclass(frozen=True, slots=True)
class PreparedDraftAdmission:
    verified: object
    observations: tuple


class DraftAdmissionGuard:
    def __init__(self, engine, universes, eligibility=None):
        self.material = ValidationMaterial(engine)
        self.universes = MappingProxyType(dict(universes))
        self.eligibility = eligibility

    def prepare(self, scope, request):
        verified = self.material.load(scope, request.draft.validation_id)
        verified.require_selection(request)
        universe = self.universes.get((scope.tenant_id, scope.project_id))
        ensure(universe is not None and universe.sha256 == verified.universe.sha256, "draft_universe_changed")
        ensure(not verified.entry.descriptors or self.eligibility is not None, "draft_tool_eligibility_unavailable")
        observations = self.eligibility.observe(verified) if verified.entry.descriptors else ()
        ensure(len(observations) == len(verified.entry.plan.document.lock.tools), "draft_tool_eligibility_incomplete")
        return PreparedDraftAdmission(verified, observations)

    def check(self, conn, scope, request, prepared):
        verified = prepared.verified
        params = {"tenant": scope.tenant_id, "project": scope.project_id, "draft": request.draft.draft_id}
        row = conn.execute(text("SELECT head_revision FROM runtime.definition_heads WHERE " + storage.KEY + " FOR UPDATE"), params).mappings().one_or_none()
        ensure(row is not None and row["head_revision"] == request.draft.revision, "draft_head_changed")
        universe = self.universes.get((scope.tenant_id, scope.project_id))
        ensure(universe is not None and universe.sha256 == verified.universe.sha256, "draft_universe_changed")
        now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
        for observation in prepared.observations:
            observation.require_fresh(now)
        return verified.require_selection(request)

    @staticmethod
    def record(conn, params, run_id, operation_id, prepared):
        verified = prepared.verified
        conn.execute(text("INSERT INTO runtime.definition_admissions "
            "(tenant_id,project_id,run_id,plan_sha256,validation_id,operation_id) "
            "VALUES (:tenant,:project,:run,:plan,:validation,:operation)"),
            {**params, "run": run_id, "plan": verified.entry.plan.sha256,
             "validation": verified.validation.validation_id, "operation": operation_id})

        if prepared.observations:
            payload = {"kind": "draft_eligibility_observed", "run_id": run_id,
                       "profile": ("structural-registry-observation-v1" if verified.universe.profile == "amphora-authoring-universe-v2"
                                   else "synthetic-registry-observation-v1"), "reservation": False,
                       "observations": [item.record() for item in prepared.observations]}
            conn.execute(text("INSERT INTO runtime.audit_events "
                "(event_id,tenant_id,project_id,run_id,revision,ordinal,payload) "
                "VALUES (:event,:tenant,:project,:run,0,1,CAST(:payload AS jsonb))"),
                {**params, "event": uuid.uuid4().hex, "run": run_id, "payload": json.dumps(payload)})
