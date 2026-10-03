"""Focused route registration reuses Research's bounded authenticated JSON transport."""
from amphora_contracts_research import (
    AssessObservationUseRequest,
    InterpretationImpactRequest,
    InterpretationSelection,
    MaterialStateImpactRequest,
    MaterialStateRevisionRef,
    NormalizeObservationRequest,
    ObservationRevisionRef,
)


def attach(register, operations):
    for path,model,operation in (
        ("observation-normalizations",NormalizeObservationRequest,operations.normalize),
        ("observation-uses",AssessObservationUseRequest,operations.assess_use),
        ("observation-interpretations/read",InterpretationSelection,operations.read),
        ("observation-corrections/read",ObservationRevisionRef,operations.observation_correction),
        ("material-state-corrections/read",MaterialStateRevisionRef,operations.material_correction),
        ("material-state-impact",MaterialStateImpactRequest,operations.material_impact),
        ("interpretation-impact",InterpretationImpactRequest,operations.interpretation_impact),
    ):
        register("/v1/"+path,model,operation)
