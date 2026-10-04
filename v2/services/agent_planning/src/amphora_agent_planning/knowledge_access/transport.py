"""Closed Knowledge read profile; wire errors and limits retain v0.18 behavior."""

from amphora_contracts_knowledge import (
    AcceptedChangeRef,
    AcceptedGraphChange,
    DomainGraphRef,
    DomainGraphSnapshot,
    DomainRevisionRef,
    GraphAuthoringProfile,
)

from ..peer_reads.profile import PeerUnavailable, ReadProfile, ReadWindow
from ..peer_reads.transport import BoundedReadTransport

PROFILE = ReadProfile("knowledge", 15, 3, 18087936, {
    "/v1/graph-profiles/read": (DomainGraphRef, GraphAuthoringProfile, 262144),
    "/v1/graph-snapshots/read": (DomainRevisionRef, DomainGraphSnapshot, 16777216),
    "/v1/graph-changes/read": (AcceptedChangeRef, AcceptedGraphChange, 1048576),
})
KnowledgeUnavailable = PeerUnavailable


class KnowledgeReadWindow(ReadWindow):
    def __init__(self, seconds=15):
        super().__init__(PROFILE, seconds)


class KnowledgeTransport(BoundedReadTransport):
    def __init__(self, endpoint, token):
        super().__init__(endpoint, token, PROFILE)
