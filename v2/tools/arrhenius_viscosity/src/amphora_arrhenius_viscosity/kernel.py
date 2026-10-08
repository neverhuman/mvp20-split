"""Narrow port of v1 arrhenius_viscosity, not the complete viscosity model."""
from dataclasses import dataclass
import math
from .payloads import ViscosityInput, ViscosityOutput

GAS_CONSTANT_J_MOL_K = 8.31446261815324

@dataclass(frozen=True)
class TemperatureAdjustment:
    parameters: ViscosityInput

    def observation(self) -> ViscosityOutput:
        p = self.parameters
        reference = p.reference_temperature_c + 273.15
        temperature = p.temperature_c + 273.15
        exponent = p.activation_energy_j_mol / GAS_CONSTANT_J_MOL_K * (1 / temperature - 1 / reference)
        try:
            viscosity = p.reference_viscosity_pa_s * math.exp(exponent)
        except OverflowError as error:
            raise ValueError('nonfinite_result') from error
        if not math.isfinite(viscosity) or viscosity <= 0:
            raise ValueError('nonpositive_or_nonfinite_result')
        return ViscosityOutput(candidate_id=p.candidate_id, input_parameters=p,
            reference_temperature_k=reference, temperature_k=temperature,
            exponent=exponent, viscosity_pa_s=viscosity,
            procedure=('Validate positive reference viscosity and activation energy; check temperature bounds.',
                       'Convert temperatures from degrees C to K using +273.15.',
                       'eta(T) = eta(reference)*exp(Ea/R*(1/T-1/T_reference)).'),
            limitation='Temperature adjustment from supplied parameters, not a validated formulation prediction. No shear-rate, cure, mixture or bioavailability inference. Process target is not supplied.')

def compute(payload: bytes) -> bytes:
    if len(payload) > 262144:
        raise ValueError('payload_too_large')
    return TemperatureAdjustment(ViscosityInput.model_validate_json(payload)).observation().model_dump_json().encode()
