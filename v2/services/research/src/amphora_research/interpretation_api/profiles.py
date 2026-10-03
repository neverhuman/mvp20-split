"""Active reviewed interpretation profiles admit new jobs; stored intents own all retries."""
from ..observations.identity import require
from ..observations.interpretation.profiles import InterpretationProfile


class InterpretationProfiles:
    def __init__(self, profiles=()):
        require(type(profiles) is tuple and len(profiles) <= 32,"interpretation_profile_limit")
        self._profiles = {}
        for profile in profiles:
            require(type(profile) is InterpretationProfile,"interpretation_profile_required")
            profile = InterpretationProfile.from_wire(profile.to_wire())
            require(profile.reference not in self._profiles,"duplicate_interpretation_profile")
            self._profiles[profile.reference] = profile

    def select(self, reference):
        profile = self._profiles.get(reference)
        require(profile is not None,"interpretation_profile_unavailable")
        return profile
