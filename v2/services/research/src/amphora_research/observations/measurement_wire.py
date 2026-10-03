"""Explicit DTO mapping reruns measurement invariants; shape success is not semantic acceptance."""
from amphora_contracts_research import (
    CategoricalMeasurement,
    CensorBound,
    CensoredMeasurement,
    MeasurementInterval,
    MeasurementQuantity,
    MissingMeasurement,
    NumericMeasurement,
    SeriesMeasurement,
    SeriesMeasurementPoint,
)

from . import (
    CategoryValue,
    CensoredValue,
    CensorLimit,
    DecimalValue,
    MissingValue,
    NumericValue,
    Quantity,
    ReportedInterval,
    SeriesPoint,
    SeriesValue,
)
from .quantities import MeasurementError


def quantity_to_wire(value):
    return MeasurementQuantity(value=value.value.text,unit=value.unit)


def quantity_from_wire(record):
    return Quantity(DecimalValue(record.value),record.unit)


def interval_to_wire(value):
    return None if value is None else MeasurementInterval(
        lower=quantity_to_wire(value.lower),upper=quantity_to_wire(value.upper),description=value.description)


def interval_from_wire(record):
    return None if record is None else ReportedInterval(
        quantity_from_wire(record.lower),quantity_from_wire(record.upper),record.description)


def bound_to_wire(value):
    return None if value is None else CensorBound(quantity=quantity_to_wire(value.quantity),inclusive=value.inclusive)


def bound_from_wire(record):
    return None if record is None else CensorLimit(quantity_from_wire(record.quantity),record.inclusive)


def to_wire(value):
    if type(value) is NumericValue:
        return NumericMeasurement(kind="numeric",quantity=quantity_to_wire(value.quantity),uncertainty=interval_to_wire(value.uncertainty))
    if type(value) is CensoredValue:
        return CensoredMeasurement(kind="censored",lower=bound_to_wire(value.lower),upper=bound_to_wire(value.upper))
    if type(value) is CategoryValue:
        return CategoricalMeasurement(kind="categorical",label=value.label)
    if type(value) is MissingValue:
        return MissingMeasurement(kind="missing",reason=value.reason)
    if type(value) is SeriesValue:
        return SeriesMeasurement(kind="series",x_unit=value.x_unit,y_unit=value.y_unit,
            points=tuple(SeriesMeasurementPoint(x=quantity_to_wire(point.x),y=to_wire(point.y)) for point in value.points))
    raise MeasurementError("unsupported_measurement_value")


def from_wire(record):
    if type(record) is NumericMeasurement:
        return NumericValue(quantity_from_wire(record.quantity),interval_from_wire(record.uncertainty))
    if type(record) is CensoredMeasurement:
        return CensoredValue(bound_from_wire(record.lower),bound_from_wire(record.upper))
    if type(record) is CategoricalMeasurement:
        return CategoryValue(record.label)
    if type(record) is MissingMeasurement:
        return MissingValue(record.reason)
    if type(record) is SeriesMeasurement:
        return SeriesValue(record.x_unit,record.y_unit,
                           tuple(SeriesPoint(quantity_from_wire(point.x),from_wire(point.y)) for point in record.points))
    raise MeasurementError("unsupported_measurement_record")
