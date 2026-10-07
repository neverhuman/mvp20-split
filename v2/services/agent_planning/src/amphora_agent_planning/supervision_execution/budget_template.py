"""Acyclic reviewed configuration derives the unchanged per-request budget policy."""

import hashlib
import json
from dataclasses import dataclass
from typing import Annotated, Literal

from amphora_contracts_core import (
    ArtifactRef,
    SafePositiveInt,
    SchemaRef,
    Scope,
    WireModel,
)
from amphora_contracts_planning import (
    CallLimits,
    ModelBinding,
    ProposalAction,
    checkpoint_draft_schema,
    checkpoint_followup_draft_schema,
)
from pydantic import Field

from ..budget import BudgetPolicy
from ..context import AttemptBinding, RequestSnapshot
from ..context.policy import require
from ..context.snapshot import _constant, _object


class TemplateRecord(WireModel):
    profile: Literal['planning-supervision-budget-template.v1'] = 'planning-supervision-budget-template.v1'
    scope: Scope
    model: ModelBinding
    prompt: ArtifactRef
    output_schema: SchemaRef
    allowed_actions: Annotated[tuple[ProposalAction, ...], Field(min_length=1, max_length=4)]
    limits: CallLimits
    per_attempt_accounting_units: SafePositiveInt


def encoded(record):
    return json.dumps(record.model_dump(mode='json'), sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def read(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 16384, 'budget_template_size')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
    return TemplateRecord.model_validate_json(json.dumps(value, allow_nan=False))


@dataclass(frozen=True)
class ReviewedBudgetTemplate:
    canonical: bytes

    def __post_init__(self):
        record = read(self.canonical)
        require(encoded(record) == self.canonical, 'noncanonical_budget_template')
        require(record.scope == record.model.configuration.scope == record.prompt.scope, 'budget_template_scope')
        require(record.output_schema in (checkpoint_draft_schema(), checkpoint_followup_draft_schema()), 'budget_template_output_profile')
        require(len(set(record.allowed_actions)) == len(record.allowed_actions), 'budget_template_actions')
        tokens = record.limits.max_input_tokens + record.limits.max_output_tokens
        require(tokens <= record.model.context_window_tokens and tokens <= record.limits.total_tokens,
                'budget_template_tokens')
        require(record.per_attempt_accounting_units <= record.limits.total_accounting_units, 'budget_template_accounting')

    @classmethod
    def from_bytes(cls, raw):
        return cls(encoded(read(raw)))

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def document(self):
        return TemplateRecord.model_validate_json(self.canonical)

    def require_reference(self, reference):
        reference = ArtifactRef.model_validate_json(reference.model_dump_json())
        require(reference.scope == self.document().scope and reference.sha256 == self.sha256 and
                reference.size_bytes == len(self.canonical) and reference.media_type == 'application/json',
                'budget_template_artifact')

    def bind(self, request):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        record = self.document()
        require(original.reference.scope == record.scope and original.purpose == 'supervision', 'budget_template_request')
        data = record.model_dump(mode='json')
        data.pop('profile')
        data.pop('scope')
        data.update(format='planning-budget-policy.v1', policy=original.context.policy.model_dump(mode='json'))
        policy = BudgetPolicy.from_bytes(json.dumps(data, allow_nan=False).encode('utf-8'))
        policy.demand(AttemptBinding(request, 1))
        return policy
