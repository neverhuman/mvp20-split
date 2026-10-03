"""All-or-none derived measurements; originals, censoring and source order remain intact."""
from dataclasses import dataclass

from amphora_contracts_core import SchemaRef

from ..quantities import unit_token
from ..series import SeriesPoint, SeriesValue
from ..values import CategoryValue, CensoredValue, CensorLimit, MissingValue, NumericValue, ReportedInterval
from .catalog import ConversionCatalog, ConversionRule, NormalizationUnavailable, require

MEASUREMENTS = (NumericValue,CensoredValue,CategoryValue,MissingValue,SeriesValue)


@dataclass(frozen=True, slots=True)
class NormalizationTargets:
    value_unit: str
    coordinate_unit: str | None = None

    def __post_init__(self):
        unit_token(self.value_unit)
        if self.coordinate_unit is not None:
            unit_token(self.coordinate_unit)


@dataclass(frozen=True, slots=True)
class NormalizedMeasurement:
    original: object
    targets: NormalizationTargets
    policy: SchemaRef
    normalized: object | None
    applied: tuple[ConversionRule, ...]
    reason: str | None

    @property
    def status(self):
        return "unresolved" if self.normalized is None else "normalized"

    @classmethod
    def evaluate(cls, catalog, original, targets):
        require(type(catalog) is ConversionCatalog,"normalization_catalog_required")
        require(type(original) in MEASUREMENTS,"normalization_measurement_required")
        require(type(targets) is NormalizationTargets,"normalization_targets_required")
        try:
            normalized,applied = _transform(catalog,original,targets)
            return cls(original,targets,catalog.reference,normalized,applied,None)
        except NormalizationUnavailable as error:
            return cls(original,targets,catalog.reference,None,(),str(error))


def _scalar(value, rule):
    if rule is None or type(value) is MissingValue:
        return value
    if type(value) is NumericValue:
        uncertainty = value.uncertainty
        if uncertainty is not None:
            uncertainty = ReportedInterval(rule.apply(uncertainty.lower),rule.apply(uncertainty.upper),uncertainty.description)
        return NumericValue(rule.apply(value.quantity),uncertainty)
    lower,upper = value.lower,value.upper
    return CensoredValue(None if lower is None else CensorLimit(rule.apply(lower.quantity),lower.inclusive),
        None if upper is None else CensorLimit(rule.apply(upper.quantity),upper.inclusive))


def _transform(catalog, original, targets):
    if type(original) in (MissingValue,CategoryValue):
        raise NormalizationUnavailable("normalization_"+original.kind)
    if type(original) is not SeriesValue:
        if targets.coordinate_unit is not None:
            raise NormalizationUnavailable("normalization_coordinate_requires_series")
        rule = catalog.select(original.unit,targets.value_unit)
        return _scalar(original,rule),() if rule is None else (rule,)
    value_rule = catalog.select(original.y_unit,targets.value_unit)
    coordinate_rule = None if targets.coordinate_unit is None else catalog.select(original.x_unit,targets.coordinate_unit)
    points = tuple(SeriesPoint(point.x if coordinate_rule is None else coordinate_rule.apply(point.x),_scalar(point.y,value_rule))
        for point in original.points)
    result = SeriesValue(targets.coordinate_unit or original.x_unit,targets.value_unit,points)
    return result,tuple(dict.fromkeys(rule for rule in (coordinate_rule,value_rule) if rule is not None))
