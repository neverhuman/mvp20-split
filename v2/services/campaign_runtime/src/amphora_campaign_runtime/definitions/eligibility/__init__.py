"""Bounded Registry observations for draft admission, never reservations."""

from .client import RegistryEligibility
from .observations import EligibilityObservation, EligibilityUnavailable

__all__ = ["EligibilityObservation", "EligibilityUnavailable", "RegistryEligibility"]
