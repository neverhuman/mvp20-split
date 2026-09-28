"""Tool-owned payload DTOs; no runtime or other scientific representation."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Operand = Annotated[float, Field(ge=-1e100, le=1e100)]


class AffineInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, allow_inf_nan=False)
    schema_version: Literal["1"] = "1"
    values: Annotated[tuple[Operand, ...], Field(max_length=1024)]
    a: Operand
    b: Operand


class AffineOutput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, allow_inf_nan=False)
    schema_version: Literal["1"] = "1"
    values: Annotated[tuple[float, ...], Field(max_length=1024)]
