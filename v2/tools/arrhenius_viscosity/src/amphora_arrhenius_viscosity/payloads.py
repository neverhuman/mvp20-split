"""Explicit units and strictly bounded tool input; no hidden default parameters."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field

class Record(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', frozen=True, allow_inf_nan=False)

class ViscosityInput(Record):
    schema_version: Literal['1'] = '1'
    candidate_id: Annotated[str, Field(min_length=1, max_length=128)]
    parameter_context: Annotated[str, Field(min_length=1, max_length=2048)]
    reference_viscosity_pa_s: Annotated[float, Field(gt=0, le=1e100)]
    reference_temperature_c: Annotated[float, Field(ge=-273.14, le=500)]
    temperature_c: Annotated[float, Field(ge=-273.14, le=500)]
    activation_energy_j_mol: Annotated[float, Field(gt=0, le=1e100)]

class ViscosityOutput(Record):
    schema_version: Literal['1'] = '1'
    candidate_id: str
    scientific_status: Literal['unvalidated_screen'] = 'unvalidated_screen'
    input_parameters: ViscosityInput
    reference_temperature_k: float
    temperature_k: float
    exponent: float
    viscosity_pa_s: float
    procedure: tuple[str, ...]
    limitation: str
