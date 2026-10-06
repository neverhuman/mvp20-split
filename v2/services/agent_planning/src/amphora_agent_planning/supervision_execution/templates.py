"""Only exact operator-reviewed template Artifacts may generate a budget policy."""

from types import MappingProxyType

from amphora_contracts_core import ArtifactRef

from ..context.policy import require
from .budget_template import ReviewedBudgetTemplate


class BudgetTemplates:
    def __init__(self, entries):
        selected = {}
        for reference, supplied in entries:
            reference = ArtifactRef.model_validate_json(reference.model_dump_json())
            template = ReviewedBudgetTemplate(supplied.canonical)
            template.require_reference(reference)
            key = (reference.scope.tenant_id, reference.scope.project_id, reference.artifact_id)
            require(key not in selected, 'duplicate_budget_template')
            selected[key] = (reference, template)
        self._entries = MappingProxyType(selected)

    def require(self, reference):
        reference = ArtifactRef.model_validate_json(reference.model_dump_json())
        selected = self._entries.get((reference.scope.tenant_id, reference.scope.project_id, reference.artifact_id))
        require(selected is not None and selected[0] == reference, 'budget_template_unavailable')
        return selected[1]
