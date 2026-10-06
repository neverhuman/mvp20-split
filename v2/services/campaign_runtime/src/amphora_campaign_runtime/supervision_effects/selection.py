"""Immutable concrete scalar selection with exact original-value revalidation."""

import hashlib
from dataclasses import dataclass
from typing import Annotated, Literal

from amphora_contracts_campaigns import ActivationPath
from amphora_contracts_core import Digest, Identifier, WireModel
from amphora_contracts_graph_runtime import GraphBinding, ScalarValue
from pydantic import Field, TypeAdapter

from ..compiler.catalog import canonical
from ..supervision_checkpoints.values import ValueCheckpointSeed, read_seed
from ..supervision_policy import ReviewedPolicy, ScalarRule
from ..supervision_requests.binding import encoded
from ..supervision_scope.observations import require

_SCALAR = TypeAdapter(ScalarValue)


def scalar_digest(value):
    value = _SCALAR.validate_json(value.model_dump_json())
    return hashlib.sha256(canonical(value.model_dump(mode='json'))).hexdigest()


class FieldChange(WireModel):
    name: Identifier
    previous_value_sha256: Digest
    value: ScalarValue


class SelectionRecord(WireModel):
    profile: Literal['runtime-supervision-scalar-selection.v1'] = 'runtime-supervision-scalar-selection.v1'
    decision_id: Digest
    seed_sha256: Digest
    target: ActivationPath
    changes: Annotated[tuple[FieldChange, ...], Field(min_length=1, max_length=64)]


@dataclass(frozen=True)
class ScalarSelection:
    canonical: bytes
    seed: ValueCheckpointSeed

    def __post_init__(self):
        require(type(self.canonical) is bytes and 0 < len(self.canonical) <= 262144, 'selection_size')
        policy = ReviewedPolicy(self.seed.policy.canonical, self.seed.policy.plan)
        seed = read_seed(self.seed.canonical, policy)
        require(isinstance(seed, ValueCheckpointSeed), 'selection_requires_scalar_seed')
        object.__setattr__(self, 'seed', seed)
        record, original = self.document(), seed.document()
        require(encoded(record) == self.canonical, 'noncanonical_scalar_selection')
        require(record.decision_id == seed.decision_id and record.seed_sha256 == seed.sha256,
                'selection_seed_binding')
        target = original.snapshot.checkpoints[0]
        require(target.kind == 'artifact_materialize', 'selection_target_kind')
        path = next(item.node.path for item in original.observations if item.node.activation_id == target.activation_id)
        require(record.target == path, 'selection_target_occurrence')
        names = tuple(change.name for change in record.changes)
        require(names == tuple(sorted(set(names))), 'selection_field_order_or_duplicate')
        fields = {binding.port: binding.value for binding in original.original_fields}
        rule = policy.rule_for(path)
        permits = {field.name: ScalarRule(field) for field in rule.fields}
        for change in record.changes:
            require(change.name in fields and change.name in permits, 'selection_field_not_permitted')
            require(change.previous_value_sha256 == scalar_digest(fields[change.name]), 'selection_prior_value')
            permits[change.name].require_allowed(change.value)

    @classmethod
    def bind(cls, seed, target, changes):
        record = SelectionRecord(decision_id=seed.decision_id, seed_sha256=seed.sha256, target=target,
                                 changes=tuple(sorted(changes, key=lambda item: item.name)))
        return cls(encoded(record), seed)

    def document(self):
        return SelectionRecord.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def resolve(self, original_fields):
        """Overlay only after exact selected original fields match; retain every other field."""
        fields = tuple(GraphBinding.model_validate_json(item.model_dump_json()) for item in original_fields)
        require(len({item.port for item in fields}) == len(fields), 'selection_duplicate_original')
        values = {item.port: item.value for item in fields}
        for binding in self.seed.document().original_fields:
            require(binding.port in values and scalar_digest(values[binding.port]) == scalar_digest(binding.value),
                    'selection_current_original_mismatch')
        changes = {item.name: item.value for item in self.document().changes}
        return tuple(GraphBinding(port=item.port, value=changes.get(item.port, item.value)) for item in fields)
