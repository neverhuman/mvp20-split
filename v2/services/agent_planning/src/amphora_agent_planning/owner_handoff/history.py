"""Bind a handoff to exact owned task, observation and finalized interpretation."""

from ..publication.origin import PublishedHistory
from .selection import HandoffSelection


class HandoffHistory(PublishedHistory):
    @classmethod
    def load(cls, connection, principal, selection, trace_journal):
        selection = HandoffSelection.restore(selection.canonical, principal)
        return cls._load(connection, principal, selection, trace_journal, "handoff")
