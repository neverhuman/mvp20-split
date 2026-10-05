"""Finite reviewed scalar targets; no Runtime read or write is performed."""

from dataclasses import dataclass

from ..context.policy import require


def target_key(value):
    return value.target.scope_path, value.target.node_id, value.input_name


@dataclass(frozen=True)
class AdjustmentPermissions:
    permits: tuple

    @classmethod
    def bind(cls, permits):
        require(len({target_key(item) for item in permits}) == len(permits), 'decision_duplicate_adjustment')
        for permit in permits:
            bounds = permit.bounds
            if bounds.kind == 'enumeration':
                require(len(set(bounds.values)) == len(bounds.values), 'decision_duplicate_scalar')
            else:
                require(bounds.minimum <= bounds.maximum, 'decision_numeric_range')
        return cls(permits)

    def validate(self, candidate):
        require(self.bind(self.permits) == self, 'decision_adjustment_binding')
        permits = {target_key(permit): permit for permit in self.permits}
        for change in candidate.changes:
            permit = permits.get(target_key(change))
            require(permit is not None, 'decision_adjustment_target')
            require(change.previous_value_sha256 == permit.previous_value_sha256, 'decision_adjustment_previous')
            bounds, proposed = permit.bounds, change.proposed
            if bounds.kind == 'enumeration':
                require(proposed in bounds.values, 'decision_adjustment_value')
            else:
                require(proposed.kind == bounds.scalar and proposed.unit == bounds.unit, 'decision_adjustment_type_or_unit')
                require(bounds.minimum <= proposed.value <= bounds.maximum, 'decision_adjustment_range')
