"""Immutable Runtime-owned configuration; no publication or model authority."""

import hashlib
from dataclasses import dataclass
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Scope, WireModel
from amphora_contracts_planning import (
    CallLimits,
    ContextEntry,
    ContextOmission,
    ModelBinding,
    ProposalAction,
    checkpoint_draft_schema,
)
from pydantic import Field

from ..compiler.catalog import canonical
from ..supervision_scope.observations import require


class RecipeRecord(WireModel):
    profile: Literal['runtime-supervision-recipe.v1'] = 'runtime-supervision-recipe.v1'
    scope: Scope
    objective: ArtifactRef
    prompt: ArtifactRef
    model: ModelBinding
    budget_policy: ArtifactRef
    entries: Annotated[tuple[ContextEntry, ...], Field(max_length=127)]
    omissions: Annotated[tuple[ContextOmission, ...], Field(max_length=128)]
    allowed_actions: Annotated[tuple[ProposalAction, ...], Field(min_length=1, max_length=4)]
    limits: CallLimits


@dataclass(frozen=True)
class ReviewedRecipe:
    canonical: bytes

    def __post_init__(self):
        require(type(self.canonical) is bytes and 0 < len(self.canonical) <= 262144, 'recipe_size')
        record = self.document()
        require(canonical(record.model_dump(mode='json')) == self.canonical, 'noncanonical_recipe')
        bases = (record.objective, record.prompt, record.model.configuration, record.budget_policy)
        included = (*bases, *(item.artifact for item in record.entries))
        omitted = tuple(item.artifact for item in record.omissions)
        identities = {}
        for ref in (*included, *omitted):
            require(ref.scope == record.scope, 'recipe_artifact_scope')
            require(identities.setdefault(ref.artifact_id, ref) == ref, 'recipe_artifact_identity')
        entry_ids = [item.artifact.artifact_id for item in record.entries]
        omitted_ids = [ref.artifact_id for ref in omitted]
        require(len(set(entry_ids)) == len(entry_ids), 'recipe_duplicate_entry')
        require(len(set(omitted_ids)) == len(omitted_ids), 'recipe_duplicate_omission')
        require(not set(omitted_ids).intersection(ref.artifact_id for ref in included), 'recipe_included_omission')
        require(len(set(record.allowed_actions)) == len(record.allowed_actions), 'recipe_duplicate_action')
        per_call = record.limits.max_input_tokens + record.limits.max_output_tokens
        require(per_call <= record.model.context_window_tokens, 'recipe_context_window')
        require(per_call <= record.limits.total_tokens, 'recipe_attempt_budget')

    @classmethod
    def bind(cls, record):
        checked = RecipeRecord.model_validate_json(record.model_dump_json())
        return cls(canonical(checked.model_dump(mode='json')))

    def document(self):
        return RecipeRecord.model_validate_json(self.canonical)

    def require_policy(self, policy):
        record = policy.document()
        require(record.profile == 'runtime-supervision-policy.v2', 'recipe_policy_profile')
        require(record.scope == self.document().scope and record.context_recipe_sha256 == self.sha256,
                'recipe_policy_binding')
        require(all(self.document().limits.max_attempts <= rule.max_model_calls for rule in record.checkpoints),
                'recipe_policy_attempts')

    def require_context(self, context, declaration_sha256):
        record = self.document()
        for name in ('scope', 'objective', 'prompt', 'model', 'omissions'):
            require(getattr(context, name) == getattr(record, name), 'recipe_context_binding')
        require(context.output_schema == checkpoint_draft_schema(), 'recipe_output_profile')
        require(set(context.allowed_actions) <= set(record.allowed_actions), 'recipe_actions_widened')
        require(context.limits.accounting_unit == record.limits.accounting_unit, 'recipe_accounting_unit')
        for name in ('max_input_tokens', 'max_output_tokens', 'max_attempts', 'total_tokens', 'total_accounting_units'):
            require(getattr(context.limits, name) <= getattr(record.limits, name), 'recipe_limits_widened')
        require(context.entries[:-1] == record.entries and len(context.entries) == len(record.entries) + 1,
                'recipe_static_context')
        declaration = context.entries[-1]
        require(declaration.role == 'constraint' and declaration.required and
                declaration.artifact.sha256 == declaration_sha256, 'recipe_declaration_context')
        static = (record.objective, record.prompt, record.model.configuration, context.policy,
                  *(entry.artifact for entry in record.entries), *(item.artifact for item in record.omissions))
        require(declaration.artifact.artifact_id not in {item.artifact_id for item in static},
                'recipe_declaration_identity')

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
