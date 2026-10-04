"""Campaign-bound, explicitly paged Research exploration reads."""

from .page import ViewPage
from .query import ViewSelection
from .reader import ResearchViewReader, ViewReadResult
from .transport import ResearchViewTransport, ResearchViewWindow

__all__ = ["ResearchViewReader", "ResearchViewTransport", "ResearchViewWindow", "ViewPage", "ViewReadResult", "ViewSelection"]
