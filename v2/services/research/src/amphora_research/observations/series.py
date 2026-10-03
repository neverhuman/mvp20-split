"""Bounded source-ordered series, retaining missing/censored points and duplicate coordinates."""
from dataclasses import dataclass
from typing import ClassVar

from .quantities import MeasurementError, Quantity, unit_token
from .values import CensoredValue, MissingValue, NumericValue, quantity


@dataclass(frozen=True, slots=True)
class SeriesPoint:
    x: Quantity
    y: NumericValue | CensoredValue | MissingValue

    def __post_init__(self):
        quantity(self.x)
        if type(self.y) not in (NumericValue, CensoredValue, MissingValue):
            raise MeasurementError("invalid_series_value")


@dataclass(frozen=True, slots=True)
class SeriesValue:
    x_unit: str
    y_unit: str
    points: tuple[SeriesPoint, ...]
    kind: ClassVar[str] = "series"

    @property
    def reported_count(self):
        return sum(type(point.y) is not MissingValue for point in self.points)

    def __post_init__(self):
        unit_token(self.x_unit)
        unit_token(self.y_unit)
        if type(self.points) is not tuple or not 1 <= len(self.points) <= 4096:
            raise MeasurementError("series_point_bound")
        for point in self.points:
            if type(point) is not SeriesPoint:
                raise MeasurementError("series_point_required")
            if point.x.unit != self.x_unit or (type(point.y) is not MissingValue and point.y.unit != self.y_unit):
                raise MeasurementError("series_unit_mismatch")
