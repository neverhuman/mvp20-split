"""Exact reported decimal text and opaque units, with explicit resource bounds."""
import re
from dataclasses import dataclass
from decimal import Decimal

DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE]([+-]?[0-9]+))?\Z")


class MeasurementError(ValueError):
    pass


def unit_token(value):
    if type(value) is not str or not 1 <= len(value) <= 32 or not value.isprintable() or any(c.isspace() for c in value):
        raise MeasurementError("invalid_measurement_unit")


@dataclass(frozen=True, slots=True)
class DecimalValue:
    text: str

    def __post_init__(self):
        if type(self.text) is not str or not 1 <= len(self.text) <= 128:
            raise MeasurementError("invalid_decimal_text")
        match = DECIMAL.fullmatch(self.text)
        if match is None:
            raise MeasurementError("invalid_decimal_text")
        if match.group(1) is not None and abs(int(match.group(1))) > 128:
            raise MeasurementError("decimal_exponent_bound")
        parts = self.amount.as_tuple()
        if len(parts.digits) > 64 or abs(parts.exponent) > 128:
            raise MeasurementError("decimal_precision_bound")

    @property
    def amount(self):
        # Decimal construction is exact and does not round to the ambient context.
        return Decimal(self.text)


@dataclass(frozen=True, slots=True)
class Quantity:
    value: DecimalValue
    unit: str

    def __post_init__(self):
        if type(self.value) is not DecimalValue:
            raise MeasurementError("exact_decimal_required")
        unit_token(self.unit)
