"""Reviewed active profiles admit new work; stored intents own historical configuration."""
from ..observations.reports import ConfiguredLabReturn
from .boundary import ConfiguredScientificInput, require


class ReviewedProfiles:
    def __init__(self, profiles=()):
        self._profiles = {}
        for configured in profiles:
            require(type(configured) in (ConfiguredScientificInput,ConfiguredLabReturn),"scientific_profile_type")
            configured = type(configured)(configured.document)
            reference = configured.reference
            require(reference not in self._profiles,"duplicate_scientific_profile")
            self._profiles[reference] = configured

    def select(self, reference):
        configured = self._profiles.get(reference)
        require(configured is not None,"scientific_profile_unavailable")
        return configured
