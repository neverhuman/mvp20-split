"""Only exact question reads; no inferred declaration-write authority."""

from amphora_contracts_research import ResearchQuestion, ResearchQuestionRef

from ..peer_reads.profile import ReadProfile, ReadWindow
from ..peer_reads.transport import BoundedReadTransport

PROFILE = ReadProfile('research', 15, 64, 4194304, {
    '/v1/questions/read': (ResearchQuestionRef, ResearchQuestion, 1048576),
})


class ResearchReadWindow(ReadWindow):
    def __init__(self, seconds=15):
        super().__init__(PROFILE, seconds)


class ResearchTransport(BoundedReadTransport):
    def __init__(self, endpoint, token):
        super().__init__(endpoint, token, PROFILE)
