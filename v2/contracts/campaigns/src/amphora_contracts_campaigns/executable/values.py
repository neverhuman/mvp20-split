"""Version-two value types and explicit local-scope bindings; no evaluation behavior."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SchemaRef, WireModel
from pydantic import Field

Unit = Annotated[str, Field(min_length=1, max_length=64)]


class ScalarType(WireModel):
    kind: Literal["scalar"]
    scalar: Literal["boolean", "integer", "number", "string"]
    unit: Unit = "1"


class ArtifactType(WireModel):
    kind: Literal["artifact"]
    schema_ref: SchemaRef
    representation: Identifier
    unit: Unit
    media_type: Annotated[str, Field(min_length=3, max_length=128, pattern=r"^[^\s/]+/[^\s/]+$")] = "application/json"


ItemType = Annotated[ScalarType | ArtifactType, Field(discriminator="kind")]


class CollectionType(WireModel):
    kind: Literal["collection"]
    item: ItemType
    max_items: Annotated[int, Field(ge=0, le=10000)]
    missing_slots: bool = False


ValueType = Annotated[ScalarType | ArtifactType | CollectionType, Field(discriminator="kind")]


class ValuePort(WireModel):
    name: Identifier
    value_type: ValueType


class ScopeInput(WireModel):
    kind: Literal["input"]
    name: Identifier


class NodeOutput(WireModel):
    kind: Literal["output"]
    node_id: Identifier
    port: Identifier


class ScopeResult(WireModel):
    kind: Literal["result"]
    name: Identifier


class BooleanConstant(WireModel):
    kind: Literal["boolean"]
    value: bool


class IntegerConstant(WireModel):
    kind: Literal["integer"]
    value: Annotated[int, Field(ge=-9007199254740991, le=9007199254740991)]
    unit: Unit = "1"


class NumberConstant(WireModel):
    kind: Literal["number"]
    value: Annotated[float, Field(ge=-1e100, le=1e100)]
    unit: Unit = "1"


class StringConstant(WireModel):
    kind: Literal["string"]
    value: Annotated[str, Field(max_length=4096)]


class ArtifactConstant(WireModel):
    kind: Literal["artifact"]
    artifact: ArtifactRef
    representation: Identifier
    unit: Unit


ScalarConstant = Annotated[BooleanConstant | IntegerConstant | NumberConstant | StringConstant, Field(discriminator="kind")]
ValueSource = Annotated[ScopeInput | NodeOutput | ScopeResult | BooleanConstant | IntegerConstant | NumberConstant
    | StringConstant | ArtifactConstant, Field(discriminator="kind")]


class ValueBinding(WireModel):
    port: Identifier
    source: ValueSource
