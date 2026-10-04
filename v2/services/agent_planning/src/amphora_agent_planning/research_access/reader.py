"""Partial exact question availability, never a guessed latest revision."""

from ..context.policy import require
from ..extraction import ExtractionSnapshot
from ..research_proposals.context import GAP_CODES, QuestionContext
from .transport import ResearchReadWindow

STOP_CODES = frozenset({'research_access_denied', 'research_peer_unavailable', 'research_read_expired',
                       'research_read_byte_limit', 'research_read_call_limit'})


class QuestionReader:
    def __init__(self, transport):
        self.transport = transport

    def review(self, task, window=None):
        task = ExtractionSnapshot.from_bytes(task.canonical, task.request)
        window = ResearchReadWindow() if window is None else window
        records, unavailable, stopped = [], [], None
        for reference in task.document().known_questions:
            if stopped is not None:
                unavailable.append((reference, stopped))
                continue
            try:
                record = self.transport.read('/v1/questions/read', reference, window)
                require(record.reference == reference, 'research_question_binding')
                try:
                    QuestionContext.bind(task, (record,))
                except ValueError:
                    raise ValueError('research_question_invalid') from None
                window.remaining()
                records.append(record)
            except ValueError as error:
                reason = str(error)
                if reason not in GAP_CODES:
                    raise
                unavailable.append((reference, reason))
                if reason in STOP_CODES:
                    stopped = reason
        return QuestionContext.bind(task, tuple(records), tuple(unavailable))
