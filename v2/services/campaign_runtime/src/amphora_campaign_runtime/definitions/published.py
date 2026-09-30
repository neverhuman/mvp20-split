"""Resolve material for admitted runs without expanding configured admission authority."""

from sqlalchemy import text

from ..coordinator.values import ensure
from ..lifecycle.model import TransitionError
from .material import ValidationMaterial


class PublishedPlanCatalog:
    def __init__(self, engine, configured):
        self.engine, self.configured = engine, configured
        self.material = ValidationMaterial(engine)

    def require(self, scope, digest):
        try:
            return self.configured.require(scope, digest)
        except TransitionError as error:
            if str(error) != "graph_plan_unavailable":
                raise
        with self.engine.connect() as conn:
            validation = conn.execute(text("SELECT validation_id FROM runtime.definition_admissions "
                "WHERE tenant_id=:tenant AND project_id=:project AND plan_sha256=:digest ORDER BY run_id LIMIT 1"),
                {"tenant": scope.tenant_id, "project": scope.project_id, "digest": digest}).scalar_one_or_none()
        ensure(validation is not None, "graph_plan_unavailable")
        verified = self.material.load(scope, validation)
        ensure(verified.entry.plan.sha256 == digest, "published_plan_identity_mismatch")
        return verified.entry
