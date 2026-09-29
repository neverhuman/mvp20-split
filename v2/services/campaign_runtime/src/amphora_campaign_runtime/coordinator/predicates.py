"""Finite predicate evaluation over committed values; artifact reads are requested, never performed."""

from dataclasses import dataclass
from decimal import Decimal

from ..lifecycle.model import TransitionError
from .values import ensure


class ProjectionNeeded(Exception):
    def __init__(self, artifact):
        self.artifact = artifact
        super().__init__("graph_projection_required")


@dataclass(frozen=True)
class PredicateValues:
    environment: object
    artifacts: object

    def scalar(self, projection):
        source = self.environment.source(projection.source)
        if source.kind == "artifact":
            key = source.artifact.model_dump_json()
            if key not in self.artifacts:
                raise ProjectionNeeded(source.artifact)
            value = self.artifacts[key]
            if isinstance(value, TransitionError):
                raise value
            for step in projection.path:
                if isinstance(step, str):
                    ensure(isinstance(value, dict) and step in value, "projection_value_missing")
                    value = value[step]
                else:
                    ensure(isinstance(value, list) and step < len(value), "projection_value_missing")
                    value = value[step]
        else:
            ensure(not projection.path and source.kind in {"boolean", "integer", "number", "string"}, "projection_value_type")
            value = source.value
        kind = projection.value_type.scalar
        if kind in {"integer", "number"}:
            ensure(type(value) in {int, float, Decimal} or source.kind == "number" and isinstance(value, str), "projection_value_type")
            number = Decimal(str(value))
            ensure(number.is_finite(), "projection_value_nonfinite")
            ensure(kind != "integer" or number == number.to_integral_value(), "projection_value_type")
            return number
        ensure(type(value) is (bool if kind == "boolean" else str), "projection_value_type")
        return value

    def evaluate(self, predicate):
        if predicate.kind == "constant":
            return predicate.value
        if predicate.kind == "not":
            return not self.evaluate(predicate.predicate)
        if predicate.kind in {"all", "any"}:
            # Evaluate every operand: a missing committed value cannot hide behind arrival/short-circuit order.
            results = tuple(self.evaluate(child) for child in predicate.predicates)
            return all(results) if predicate.kind == "all" else any(results)
        left = self.scalar(predicate.left)
        right = predicate.right.value
        if predicate.right.kind in {"number", "integer"}:
            right = Decimal(str(right))
        match predicate.operator:
            case "eq":
                return left == right
            case "ne":
                return left != right
            case "lt":
                return left < right
            case "le":
                return left <= right
            case "gt":
                return left > right
            case "ge":
                return left >= right
        raise TransitionError("unsupported_predicate_operator")
