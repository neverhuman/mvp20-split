"""Reviewed directed scale rules; no inferred dimensions, paths, inverses or rounding."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import SchemaRef

from ..identity import identifier
from ..quantities import DecimalValue, MeasurementError, Quantity, unit_token


def require(condition, reason):
    if not condition:
        raise MeasurementError(reason)


class NormalizationUnavailable(MeasurementError):
    """Original evidence remains valid to retain; this requested transform is unresolved."""


def scaled(value, factor):
    """Multiply exact integer coefficients/exponents without Decimal context arithmetic."""
    left,right = value.amount.as_tuple(),factor.amount.as_tuple()
    coefficient = int("".join(map(str,left.digits))) * int("".join(map(str,right.digits)))
    exponent = left.exponent+right.exponent
    if coefficient == 0:
        return DecimalValue("0")
    while coefficient % 10 == 0:
        coefficient //= 10
        exponent += 1
    # A large positive exponent can still fit by retaining coefficient zeroes.
    # Reject only when no representation meets the existing digit/exponent bounds.
    if exponent > 128:
        padding = exponent-128
        if len(str(coefficient))+padding > 64:
            raise NormalizationUnavailable("normalization_output_bound")
        coefficient *= 10**padding
        exponent = 128
    sign = "-" if left.sign != right.sign else ""
    try:
        return DecimalValue(f"{sign}{coefficient}e{exponent}")
    except MeasurementError as error:
        raise NormalizationUnavailable("normalization_output_bound") from error


@dataclass(frozen=True, slots=True)
class ConversionRule:
    dimension: str
    source_unit: str
    target_unit: str
    scale: DecimalValue

    def __post_init__(self):
        identifier(self.dimension)
        unit_token(self.source_unit)
        unit_token(self.target_unit)
        require(self.source_unit != self.target_unit,"normalization_identity_rule")
        require(type(self.scale) is DecimalValue and self.scale.amount > 0,"normalization_positive_scale_required")

    def apply(self, quantity):
        require(type(quantity) is Quantity and quantity.unit == self.source_unit,"normalization_rule_source_mismatch")
        return Quantity(scaled(quantity.value,self.scale),self.target_unit)

    def descriptor(self):
        return {"dimension":self.dimension,"source_unit":self.source_unit,"target_unit":self.target_unit,"scale":self.scale.text}


@dataclass(frozen=True, slots=True)
class ConversionCatalog:
    profile_id: str
    version: str
    rules: tuple[ConversionRule, ...]

    def __post_init__(self):
        identifier(self.profile_id)
        identifier(self.version)
        require(type(self.rules) is tuple and 1 <= len(self.rules) <= 128,"normalization_rule_bound")
        require(all(type(rule) is ConversionRule for rule in self.rules),"normalization_rule_required")
        require(len({(rule.source_unit,rule.target_unit) for rule in self.rules}) == len(self.rules),"normalization_duplicate_direction")
        dimensions = {}
        for rule in self.rules:
            for unit in (rule.source_unit,rule.target_unit):
                require(unit not in dimensions or dimensions[unit] == rule.dimension,"normalization_dimension_conflict")
                dimensions[unit] = rule.dimension

    @property
    def reference(self):
        body = json.dumps({"format":"research.normalization-catalog.v1","profile_id":self.profile_id,"version":self.version,
            "rules":[rule.descriptor() for rule in self.rules]},sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
        return SchemaRef(schema_id="research.normalization",version="1",sha256=hashlib.sha256(body).hexdigest())

    def select(self, source, target):
        unit_token(source)
        unit_token(target)
        dimensions = {unit:rule.dimension for rule in self.rules for unit in (rule.source_unit,rule.target_unit)}
        if source not in dimensions or target not in dimensions:
            raise NormalizationUnavailable("normalization_unknown_unit")
        if dimensions[source] != dimensions[target]:
            raise NormalizationUnavailable("normalization_dimension_mismatch")
        if source == target:
            return None
        for rule in self.rules:
            if (rule.source_unit,rule.target_unit) == (source,target):
                return rule
        raise NormalizationUnavailable("normalization_direction_unconfigured")
