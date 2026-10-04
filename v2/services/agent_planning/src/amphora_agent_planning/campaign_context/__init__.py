"""Campaign-context values, separate from Knowledge extraction proposals."""

from .projection import ResearchContext
from .read_set import ResearchReadSet
from .records import ResearchGap, ResearchIdentity
from .selection import ResearchSelection

__all__ = ["ResearchContext", "ResearchGap", "ResearchIdentity", "ResearchReadSet", "ResearchSelection"]
