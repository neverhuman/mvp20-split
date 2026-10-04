"""One explicit read, with a safe unavailable outcome and no fabricated evidence."""

from dataclasses import dataclass

from pydantic import ValidationError

from ..campaign_research_access.reader import PEER_CODES
from ..context.policy import require
from .page import ViewPage, catalog
from .query import VIEWS, ViewSelection
from .transport import PROFILE, ResearchViewWindow

PAGE_CODES = frozenset({"research_view_response_type", "research_view_response_size", "research_view_identity",
    "research_view_scope", "research_view_window", "research_view_continuation", "research_view_observations",
    "research_view_duplicate_sample", "research_view_material", "research_view_catalog", "research_view_schema"})


@dataclass(frozen=True)
class ViewReadResult:
    selection: ViewSelection
    page: ViewPage | None
    failure: str | None
    calls: int
    bytes: int


class ResearchViewReader:
    def __init__(self, transport):
        self.transport = transport

    def read(self, selection, window=None):
        selection = ViewSelection.bind(selection.document(), selection.request)
        window = ResearchViewWindow() if window is None else window
        require(window.profile == PROFILE, "research_view_profile")
        calls, consumed = window.calls, window.consumed
        page, failure = None, None
        try:
            response = self.transport.read(VIEWS[selection.view][2], selection.document(), window)
            candidate = ViewPage.bind(selection, response)
            window.remaining()
            page = candidate
        except ValueError as error:
            if isinstance(error, ValidationError) or str(error) in PAGE_CODES:
                failure = "research_view_invalid"
            elif str(error) in PEER_CODES:
                failure = str(error)
            else:
                raise
        return ViewReadResult(selection, page, failure, window.calls - calls, window.consumed - consumed)

    def catalog(self, selection, window=None):
        selection = ViewSelection.bind(selection.document(), selection.request)
        query = selection.document()
        require(selection.view != "observation_series", "research_view_catalog_experiment")
        window = ResearchViewWindow() if window is None else window
        require(window.profile == PROFILE, "research_view_profile")
        response = self.transport.read("/v1/research-explore/catalog", query.experiment, window)
        result = catalog(response, query.experiment)
        window.remaining()
        return result
