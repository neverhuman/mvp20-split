"""Measurement transport shapes; exact decimal arithmetic and meaning belong to Research."""
import re
from typing import Annotated, Literal

from amphora_contracts_core import Identifier, WireModel
from pydantic import Field

# Compiled patterns select Python regex in Pydantic; the lookahead is also valid
# JSON Schema/ECMAScript and avoids '$' accepting an otherwise hidden final newline.
DecimalText = Annotated[str,Field(min_length=1,max_length=128,pattern=re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\s\S])"))]
UnitToken = Annotated[str,Field(min_length=1,max_length=32,pattern=re.compile(r"^\S+$(?![\s\S])"))]


class MeasurementQuantity(WireModel):
    value: DecimalText
    unit: UnitToken


class MeasurementInterval(WireModel):
    lower: MeasurementQuantity
    upper: MeasurementQuantity
    description: Annotated[str,Field(min_length=1,max_length=512)]


class NumericMeasurement(WireModel):
    kind: Literal["numeric"]
    quantity: MeasurementQuantity
    uncertainty: MeasurementInterval | None


class CensorBound(WireModel):
    quantity: MeasurementQuantity
    inclusive: bool


class CensoredMeasurement(WireModel):
    kind: Literal["censored"]
    lower: CensorBound | None
    upper: CensorBound | None


class CategoricalMeasurement(WireModel):
    kind: Literal["categorical"]
    label: Annotated[str,Field(min_length=1,max_length=256)]


class MissingMeasurement(WireModel):
    kind: Literal["missing"]
    reason: Identifier


SeriesOrdinate = Annotated[NumericMeasurement | CensoredMeasurement | MissingMeasurement,Field(discriminator="kind")]


class SeriesMeasurementPoint(WireModel):
    x: MeasurementQuantity
    y: SeriesOrdinate


class SeriesMeasurement(WireModel):
    kind: Literal["series"]
    x_unit: UnitToken
    y_unit: UnitToken
    points: Annotated[tuple[SeriesMeasurementPoint, ...],Field(min_length=1,max_length=4096)]


MeasurementValue = Annotated[NumericMeasurement | CensoredMeasurement | CategoricalMeasurement |
                           MissingMeasurement | SeriesMeasurement,Field(discriminator="kind")]
