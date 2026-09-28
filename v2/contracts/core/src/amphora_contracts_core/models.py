"""Small immutable wire primitives; no persistence, policy or provider imports."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Identifier = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
SafePositiveInt = Annotated[int, Field(ge=1, le=9007199254740991)]


class WireModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, allow_inf_nan=False)


class Scope(WireModel):
    tenant_id: Identifier
    project_id: Identifier


class SchemaRef(WireModel):
    schema_id: Identifier
    version: Literal["1"]
    sha256: Digest


class ArtifactRef(WireModel):
    artifact_id: Identifier
    scope: Scope
    sha256: Digest
    media_type: Annotated[str, Field(min_length=3, max_length=128, pattern=r"^[^\s/]+/[^\s/]+$")]
    schema_ref: SchemaRef
    size_bytes: Annotated[int, Field(ge=0, le=9007199254740991)]


class Finding(WireModel):
    code: Identifier
    location: Annotated[str, Field(max_length=256)]
    message: Annotated[str, Field(max_length=512)]
