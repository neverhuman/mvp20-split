"""Explicit synthetic symbol representation; no biological applicability inferred."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class SequenceInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, allow_inf_nan=False)
    schema_version: Literal["1"] = "1"
    sequence: Annotated[str, Field(max_length=65536, pattern=r"^[A-Za-z0-9]*$")]
    alphabet: Annotated[str, Field(min_length=1, max_length=62, pattern=r"^[A-Za-z0-9]+$")]


class SymbolCount(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    symbol: Annotated[str, Field(min_length=1, max_length=1, pattern=r"^[A-Za-z0-9]$")]
    count: Annotated[int, Field(ge=0, le=65536)]


class SequenceOutput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    schema_version: Literal["1"] = "1"
    length: Annotated[int, Field(ge=0, le=65536)]
    counts: Annotated[tuple[SymbolCount, ...], Field(min_length=1, max_length=62)]
