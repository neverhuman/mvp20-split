"""Closed named-view reads; no model-selected routes or implicit pagination."""

from amphora_contracts_research import ExperimentRevisionRef
from amphora_contracts_research_views import ResearchViewCatalog

from ..peer_reads.profile import ReadProfile, ReadWindow
from ..peer_reads.transport import BoundedReadTransport
from .query import VIEWS

PROFILE = ReadProfile("research", 20, 32, 4194304, {
    "/v1/research-explore/catalog": (ExperimentRevisionRef, ResearchViewCatalog, 1048576),
    **{path: (query, response, 1048576) for query, response, path in VIEWS.values()},
}, request_bytes=262144)


class ResearchViewWindow(ReadWindow):
    def __init__(self, seconds=20):
        super().__init__(PROFILE, seconds)


class ResearchViewTransport(BoundedReadTransport):
    def __init__(self, endpoint, token):
        super().__init__(endpoint, token, PROFILE)
