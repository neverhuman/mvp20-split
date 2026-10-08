"""Strict tool-local transport records, not domain behavior."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field

class Record(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', frozen=True, allow_inf_nan=False)

class Point(Record):
    dispersion: Annotated[float, Field(ge=0, le=1e6)]
    polar: Annotated[float, Field(ge=0, le=1e6)]
    hydrogen_bond: Annotated[float, Field(ge=0, le=1e6)]

class SolvencyInput(Record):
    schema_version: Literal['1'] = '1'
    candidate_id: Annotated[str, Field(min_length=1, max_length=128)]
    parameter_context: Annotated[str, Field(min_length=1, max_length=2048)]
    polymer: Point
    solvent: Point
    interaction_radius: Annotated[float, Field(gt=0, le=1e6)]

class SolvencyOutput(Record):
    schema_version: Literal['1'] = '1'
    candidate_id: str
    scientific_status: Literal['unvalidated_screen'] = 'unvalidated_screen'
    input_parameters: SolvencyInput
    distance_squared: float
    distance: float
    relative_energy_difference: float
    sphere_position: Literal['inside', 'boundary', 'outside']
    procedure: tuple[str, ...]
    limitation: str
