"""Exact owned result origins; shared loading preserves result error semantics."""

from ..publication.origin import PublishedHistory
from .selection import ResultSelection


class ResultHistory(PublishedHistory):
    @classmethod
    def load(cls, connection, principal, selection, trace_journal):
        selection = ResultSelection.restore(selection.canonical, principal)
        return cls._load(connection, principal, selection, trace_journal, "result")

    def arguments(self, review):
        return self.task, self.observation, review, self.interpretation
