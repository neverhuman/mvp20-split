"""Narrow port of v1 hansen_ra_squared/hansen_red; no parameter estimation."""
from dataclasses import dataclass
import math
from .payloads import SolvencyInput, SolvencyOutput

@dataclass(frozen=True)
class HansenScreen:
    parameters: SolvencyInput

    def observation(self) -> SolvencyOutput:
        p = self.parameters
        dd = p.solvent.dispersion - p.polymer.dispersion
        dp = p.solvent.polar - p.polymer.polar
        dh = p.solvent.hydrogen_bond - p.polymer.hydrogen_bond
        squared = 4 * dd * dd + dp * dp + dh * dh
        distance = math.sqrt(squared)
        red = distance / p.interaction_radius
        if not all(math.isfinite(v) for v in (squared, distance, red)):
            raise ValueError('nonfinite_result')
        return SolvencyOutput(candidate_id=p.candidate_id, input_parameters=p,
            distance_squared=squared, distance=distance, relative_energy_difference=red,
            sphere_position='inside' if red < 1 else 'outside' if red > 1 else 'boundary',
            procedure=('Validate finite nonnegative HSP parameters and positive radius.',
                       'Ra^2 = 4*(dD_s-dD_p)^2 + (dP_s-dP_p)^2 + (dH_s-dH_p)^2.',
                       'RED = sqrt(Ra^2)/R; classify position relative to the declared sphere.'),
            limitation='Calculated screen from supplied parameters, not measured compatibility. Applicability to this candidate is unestablished. No blend-parameter estimation or biological inference.')

def compute(payload: bytes) -> bytes:
    if len(payload) > 262144:
        raise ValueError('payload_too_large')
    return HansenScreen(SolvencyInput.model_validate_json(payload)).observation().model_dump_json().encode()
