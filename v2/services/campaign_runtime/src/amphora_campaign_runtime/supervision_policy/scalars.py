"""Exact type/unit and closed finite value policies, without scientific inference."""

from dataclasses import dataclass
from decimal import Decimal

from amphora_contracts_graph_runtime import ScalarValue
from pydantic import TypeAdapter

from ..compiler.catalog import canonical
from ..supervision_scope.observations import require
from .records import FieldPolicyRecord

_SCALAR = TypeAdapter(ScalarValue)


@dataclass(frozen=True)
class ScalarRule:
    record: FieldPolicyRecord

    def __post_init__(self):
        record = FieldPolicyRecord.model_validate_json(self.record.model_dump_json())
        object.__setattr__(self, 'record', record)
        shape, constraint = record.value_type, record.constraint
        numeric = shape.scalar in {'integer', 'number'}
        require(numeric or shape.unit == '1', 'policy_nonnumeric_unit')
        require(numeric == (constraint.kind == 'range'), 'policy_constraint_kind')
        if numeric:
            require(constraint.minimum.unit == constraint.maximum.unit == shape.unit, 'policy_bound_unit')
            lower, upper = Decimal(constraint.minimum.value), Decimal(constraint.maximum.value)
            require(lower.is_finite() and upper.is_finite() and lower <= upper, 'policy_bound_order')
            if shape.scalar == 'integer':
                require(lower == lower.to_integral_value() and upper == upper.to_integral_value() and
                        -9007199254740991 <= lower <= upper <= 9007199254740991, 'policy_integer_bounds')
        else:
            require(all(value.kind == shape.scalar for value in constraint.values), 'policy_choice_type')
            keys = [canonical(value.model_dump(mode='json')) for value in constraint.values]
            require(len(set(keys)) == len(keys), 'policy_duplicate_choice')

    def allows(self, value):
        value = _SCALAR.validate_json(value.model_dump_json())
        shape = self.record.value_type
        if getattr(value, 'unit', '1') != shape.unit:
            return False
        if value.kind != shape.scalar and not (shape.scalar == 'number' and value.kind == 'integer'):
            return False
        constraint = self.record.constraint
        if constraint.kind == 'range':
            return Decimal(constraint.minimum.value) <= Decimal(value.value) <= Decimal(constraint.maximum.value)
        return value in constraint.values

    def require_allowed(self, value):
        require(self.allows(value), 'scalar_adjustment_outside_policy')
