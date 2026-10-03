"""Optional reviewed interpretation profiles preserve old science configuration compatibility."""
import json

from amphora_contracts_research import NormalizationProfile, ObservationUseProfile

from ..observations.identity import require
from ..observations.interpretation.profiles import InterpretationProfile

PROFILE_FIELDS = ("normalization_profiles","observation_use_profiles")


def configured_profiles(config):
    profiles = []
    for field,model in zip(PROFILE_FIELDS,(NormalizationProfile,ObservationUseProfile),strict=True):
        values = config.get(field,[])
        require(type(values) is list and len(values) <= 32,"invalid_interpretation_profiles")
        profiles.extend(InterpretationProfile.from_wire(model.model_validate_json(json.dumps(raw))) for raw in values)
    return tuple(profiles)
