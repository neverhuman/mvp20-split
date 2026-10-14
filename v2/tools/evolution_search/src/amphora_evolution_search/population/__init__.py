"""New population domain; not activated by the existing numeric workers."""

from .specification import OriginalPopulation, canonical
from .membership import GenerationMembership

__all__ = ["OriginalPopulation", "GenerationMembership", "canonical"]
