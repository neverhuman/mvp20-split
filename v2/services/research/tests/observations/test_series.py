"""Series retain partial source order and do not guess normalization or interpolation."""
import pytest
from amphora_research.observations import (
    CategoryValue,
    CensoredValue,
    CensorLimit,
    DecimalValue,
    MeasurementError,
    MissingValue,
    NumericValue,
    Quantity,
    SeriesPoint,
    SeriesValue,
)


def q(value, unit):
    return Quantity(DecimalValue(value),unit)


def test_series_preserves_duplicate_unsorted_coordinates_and_explicit_partial_points():
    points = (SeriesPoint(q("2","s"),NumericValue(q("1.20","mg/L"))),
              SeriesPoint(q("1","s"),MissingValue("not_reported")),
              SeriesPoint(q("1","s"),CensoredValue(None,CensorLimit(q("0.1","mg/L"),False))))
    series = SeriesValue("s","mg/L",points)
    assert series.points is points
    assert [p.x.value.text for p in series.points] == ["2","1","1"]
    assert [p.y.kind for p in series.points] == ["numeric","missing","censored"]
    assert series.points[0].y.quantity.value.text == "1.20"


def test_maximum_series_is_bounded_without_deduplication():
    point = SeriesPoint(q("0","s"),MissingValue("not_reported"))
    assert len(SeriesValue("s","mg/L",(point,)*4096).points) == 4096
    with pytest.raises(MeasurementError,match="series_point_bound"):
        SeriesValue("s","mg/L",(point,)*4097)


@pytest.mark.parametrize("points", [(), [], None, [SeriesPoint(q("0","s"),MissingValue("unknown"))]])
def test_empty_or_mutable_collections_are_not_silently_fixed(points):
    with pytest.raises(MeasurementError,match="series_point_bound"):
        SeriesValue("s","mg/L",points)


@pytest.mark.parametrize("x_unit,y_unit", [("min","mg/L"),("s","g/L")])
def test_series_does_not_convert_compatible_looking_unit_labels(x_unit,y_unit):
    with pytest.raises(MeasurementError,match="series_unit_mismatch"):
        SeriesValue("s","mg/L",(SeriesPoint(q("1",x_unit),NumericValue(q("1",y_unit))),))


@pytest.mark.parametrize("value", [None, 0, CategoryValue("positive"), q("1","mg/L")])
def test_series_values_require_explicit_numeric_censored_or_missing_form(value):
    with pytest.raises(MeasurementError,match="invalid_series_value"):
        SeriesPoint(q("0","s"),value)


def test_malformed_point_and_coordinate_are_rejected():
    with pytest.raises(MeasurementError,match="series_point_required"):
        SeriesValue("s","mg/L",(None,))
    with pytest.raises(MeasurementError,match="quantity_required"):
        SeriesPoint("0",MissingValue("unknown"))
