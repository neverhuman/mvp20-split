"""Reported measurement meaning is explicit; missingness and limits never become points."""
import re
from dataclasses import dataclass
from typing import ClassVar

from .quantities import MeasurementError, Quantity


def quantity(value):
    if type(value) is not Quantity:
        raise MeasurementError("quantity_required")


def same_unit(first, second):
    if first.unit != second.unit:
        raise MeasurementError("measurement_unit_mismatch")


@dataclass(frozen=True, slots=True)
class ReportedInterval:
    lower: Quantity
    upper: Quantity
    description: str

    def __post_init__(self):
        quantity(self.lower)
        quantity(self.upper)
        same_unit(self.lower, self.upper)
        if self.lower.value.amount > self.upper.value.amount:
            raise MeasurementError("reversed_uncertainty_interval")
        if type(self.description) is not str or not self.description.strip() or len(self.description) > 512:
            raise MeasurementError("uncertainty_description_required")


@dataclass(frozen=True, slots=True)
class NumericValue:
    quantity: Quantity
    uncertainty: ReportedInterval | None = None
    kind: ClassVar[str] = "numeric"

    def __post_init__(self):
        quantity(self.quantity)
        if self.uncertainty is not None:
            if type(self.uncertainty) is not ReportedInterval:
                raise MeasurementError("reported_uncertainty_required")
            same_unit(self.quantity, self.uncertainty.lower)

    @property
    def unit(self):
        return self.quantity.unit


@dataclass(frozen=True, slots=True)
class CensorLimit:
    quantity: Quantity
    inclusive: bool

    def __post_init__(self):
        quantity(self.quantity)
        if type(self.inclusive) is not bool:
            raise MeasurementError("explicit_limit_inclusion_required")


@dataclass(frozen=True, slots=True)
class CensoredValue:
    lower: CensorLimit | None
    upper: CensorLimit | None
    kind: ClassVar[str] = "censored"

    def __post_init__(self):
        if self.lower is None and self.upper is None:
            raise MeasurementError("censor_limit_required")
        if any(limit is not None and type(limit) is not CensorLimit for limit in (self.lower, self.upper)):
            raise MeasurementError("censor_limit_required")
        if self.lower is not None and self.upper is not None:
            same_unit(self.lower.quantity, self.upper.quantity)
            low, high = self.lower.quantity.value.amount, self.upper.quantity.value.amount
            if low > high or (low == high and not (self.lower.inclusive and self.upper.inclusive)):
                raise MeasurementError("empty_censor_interval")

    @property
    def unit(self):
        return (self.lower if self.lower is not None else self.upper).quantity.unit


@dataclass(frozen=True, slots=True)
class CategoryValue:
    label: str
    kind: ClassVar[str] = "categorical"

    def __post_init__(self):
        if type(self.label) is not str or not self.label.strip() or len(self.label) > 256:
            raise MeasurementError("invalid_measurement_category")


@dataclass(frozen=True, slots=True)
class MissingValue:
    reason: str
    kind: ClassVar[str] = "missing"

    def __post_init__(self):
        if type(self.reason) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", self.reason) is None:
            raise MeasurementError("missing_reason_required")
