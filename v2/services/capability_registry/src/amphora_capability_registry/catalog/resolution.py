"""Exact-version observations are not dispatch authority or a live reservation."""

import json
from datetime import timedelta

from amphora_contracts_tools import ResolveRelease
from sqlalchemy import text

from ..descriptors.assessments import CapacityObservation
from ..structural_profiles import StructuralPolicy
from ..descriptors.policy import EligibilityEvaluator, EvaluationPolicy
from ..descriptors.requirements import CapabilityNeed, PortRequirement
from ..persistence.store import scope_bindings
from .model import RegistryDenied
from .releases import read_release


class Resolver:
    def __init__(self, resources, permissions, structural=None):
        self.resources, self.permissions = resources, permissions
        self.structural = structural or StructuralPolicy()

    def resolve(self, connection, scope, raw, factory):
        payload = ResolveRelease.model_validate_json(json.dumps(raw))
        record = read_release(connection, scope, payload.release.descriptor_sha256)
        record.document.verify_lock(payload.release)
        if record.lifecycle.status != "active":
            raise RegistryDenied("release_not_active")
        now = connection.execute(text("SELECT clock_timestamp()")).scalar_one()
        rows = connection.execute(text("SELECT r.free_slots,r.expires_at FROM registry.replicas r "
            "JOIN registry.deployments d USING(tenant_id,project_id,deployment_id) "
            "WHERE r.tenant_id=:tenant AND r.project_id=:project AND d.descriptor_sha256=:digest "
            "AND d.status='active' AND r.expires_at>:now AND r.observed_at<=:now "
            "AND d.definition->>'architecture'=:architecture AND d.definition->>'operating_system'=:os"),
            {**scope_bindings(scope), "digest": record.document.digest, "now": now,
             "architecture": self.resources.architecture, "os": self.resources.operating_system}).mappings().all()
        expiry = min((row["expires_at"] for row in rows), default=now+timedelta(seconds=1))
        capacity = CapacityObservation(scope, record.document.digest, len(rows), sum(row["free_slots"] for row in rows), now, expiry)
        need = CapabilityNeed(scope, payload.context, tuple(PortRequirement.from_port(p) for p in payload.inputs),
                              tuple(PortRequirement.from_port(p) for p in payload.outputs))
        policy = EvaluationPolicy(scope, self.resources, self.permissions, self.structural)
        decision = EligibilityEvaluator().evaluate(record.descriptor, need, policy, capacity, now=now).to_wire()
        if decision.status == "candidate":
            return factory.accepted("candidate", release=record.to_wire(scope), decision=decision)
        return factory.rejected("no_eligible_capacity", release=record.to_wire(scope), decision=decision)
