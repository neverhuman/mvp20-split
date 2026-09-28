"""Bounded graph values; no references to mutable nodes or arbitrary Python payloads."""

from typing import Annotated, Literal

from amphora_contracts_campaigns import ArtifactConstant, BooleanConstant, IntegerConstant, StringConstant
from amphora_contracts_core import Identifier, WireModel
from pydantic import Field


class NumberValue(WireModel):
    kind: Literal["number"]
    # Plain decimal strings preserve command-v1's portable, float-free identity profile.
    # At most 100 integer / 324 fractional digits, plus the exact +/-1e100 boundary.
    value: Annotated[str, Field(max_length=427, pattern=r"^-?(?:(?:0|[1-9][0-9]{0,99})(?:\.[0-9]{1,324})?|10{100})$")]
    unit: Annotated[str, Field(min_length=1, max_length=64)] = "1"


ScalarValue = Annotated[BooleanConstant | IntegerConstant | NumberValue | StringConstant, Field(discriminator="kind")]
PresentValue = Annotated[ScalarValue | ArtifactConstant, Field(discriminator="kind")]


class MissingValue(WireModel):
    kind: Literal["missing"]
    reason_code: Identifier
    member_id: Identifier


class CollectionValue(WireModel):
    kind: Literal["collection"]
    items: Annotated[tuple[PresentValue | MissingValue, ...], Field(max_length=10000)]


GraphValue = Annotated[ScalarValue | ArtifactConstant | CollectionValue, Field(discriminator="kind")]


class GraphBinding(WireModel):
    port: Identifier
    value: GraphValue
