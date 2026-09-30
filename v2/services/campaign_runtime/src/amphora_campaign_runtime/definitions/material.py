"""Restore verified immutable compilation material; never authorizes a new campaign."""

from dataclasses import dataclass

from amphora_contracts_graph_runtime import DraftValidation
from sqlalchemy import text

from ..coordinator.plans import ReviewedPlan
from ..lifecycle.model import TransitionError
from . import storage, validation_storage
from .revisions import DraftVersion
from .validation import ValidationUniverse


@dataclass(frozen=True, slots=True)
class VerifiedDraftPlan:
    draft: DraftVersion
    validation: DraftValidation
    universe: ValidationUniverse
    entry: ReviewedPlan

    def require_selection(self, request):
        """Bind a caller selection to evidence; current head and eligibility are separate checks."""
        selected = request.draft
        expected = (self.draft.draft_id, self.draft.revision, self.draft.content.sha256,
                    self.validation.validation_id, self.universe.sha256, self.entry.plan.sha256)
        actual = (selected.draft_id, selected.revision, selected.content_sha256,
                  selected.validation_id, selected.universe_sha256, request.plan_sha256)
        if actual != expected:
            raise TransitionError("draft_validation_selection_mismatch")
        return self.entry

    @classmethod
    def restore(cls, draft, validation, material):
        expected = (draft.content.definition.scope, draft.draft_id, draft.revision, draft.content.sha256)
        actual = (validation.scope, validation.draft_id, validation.revision, validation.content_sha256)
        if expected != actual:
            raise ValueError("validation_draft_identity_mismatch")
        if not validation.structurally_valid:
            raise TransitionError("draft_not_structurally_valid")
        universe = ValidationUniverse.restore(material, validation.universe_sha256)
        outcome = universe.validate(draft)
        if outcome.entry is None or outcome.to_wire(validation.validation_id) != validation:
            raise ValueError("retained_validation_compilation_mismatch")
        return cls(draft, validation, universe, outcome.entry)


class ValidationMaterial:
    """Internal Runtime repository; callers own principal checks and admission policy."""

    def __init__(self, engine):
        self.engine = engine

    def load(self, scope, validation_id):
        params = {"tenant": scope.tenant_id, "project": scope.project_id, "validation": validation_id}
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT v.*,r.record AS draft_record,u.material "
                "FROM runtime.definition_validations v JOIN runtime.definition_revisions r "
                "ON (r.tenant_id,r.project_id,r.draft_id,r.revision,r.content_sha256)="
                "(v.tenant_id,v.project_id,v.draft_id,v.revision,v.content_sha256) "
                "JOIN runtime.definition_universes u ON (u.tenant_id,u.project_id,u.universe_sha256)="
                "(v.tenant_id,v.project_id,v.universe_sha256) "
                "WHERE v.tenant_id=:tenant AND v.project_id=:project AND v.validation_id=:validation"), params).mappings().one_or_none()
        if row is None:
            raise TransitionError("graph_validation_unavailable")
        validation = validation_storage.restore(row)
        draft = storage.version({**row, "record": row["draft_record"]})
        # Hash verification and compilation happen after releasing the connection.
        return VerifiedDraftPlan.restore(draft, validation, row["material"])
