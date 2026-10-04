"""Immutable extraction inputs and byte-grounded quotations; no graph acceptance."""

from .prompt import PromptTemplate
from .snapshot import ExtractionSnapshot
from .sources import SourceBundle, SourceText

__all__ = ["ExtractionSnapshot", "PromptTemplate", "SourceBundle", "SourceText"]
