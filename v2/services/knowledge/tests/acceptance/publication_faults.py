"""Test-only process barriers; no hooks or shorter leases ship in owner wheels."""

from amphora_knowledge.publication.journal import PublicationJournal
from amphora_knowledge.publication.store import PublicationStore
from amphora_knowledge.publication.terminal import PublicationTerminals
from amphora_tool_protocol import ArtifactClient
from sqlalchemy import event

STAGES = ("reasoning_prepared", "reasoning_begin_returned", "reasoning_stream_started",
          "reasoning_stream_returned", "reasoning_stream_verified", "reasoning_finalizing",
          "reasoning_data_finalized", "reasoning_terminal_before_commit", "reasoning_terminal_committed")


def install(host, stage, barrier):
    # Exercise real database-clock expiry after process death without sleeping
    # sixty seconds per case. The replacement uses the production sixty seconds.
    acquire, renew = PublicationStore.acquire, PublicationStore.renew

    def short_acquire(self, principal, request, *, seconds=60):
        return acquire(self, principal, request, seconds=5)

    def short_renew(self, lease, *, seconds=60):
        return renew(self, lease, seconds=5)

    PublicationStore.acquire, PublicationStore.renew = short_acquire, short_renew
    if stage == "reasoning_prepared":
        original = PublicationJournal.prepare

        def prepare(self, *args):
            result = original(self, *args)
            barrier()
            return result

        PublicationJournal.prepare = prepare
    elif stage in {"reasoning_stream_started", "reasoning_stream_verified", "reasoning_finalizing"}:
        action = {"reasoning_stream_started": "streaming", "reasoning_stream_verified": "streamed",
                  "reasoning_finalizing": "finalizing"}[stage]
        original = PublicationJournal.advance

        def advance(self, lease, position, transition, receipt=None):
            result = original(self, lease, position, transition, receipt)
            if transition == action:
                barrier()
            return result

        PublicationJournal.advance = advance
    elif stage in {"reasoning_begin_returned", "reasoning_stream_returned"}:
        name = "begin_derived" if stage == "reasoning_begin_returned" else "stream"
        original = getattr(ArtifactClient, name)

        def returned(self, *args, **kwargs):
            result = original(self, *args, **kwargs)
            barrier()
            return result

        setattr(ArtifactClient, name, returned)
    elif stage in {"reasoning_data_finalized", "reasoning_terminal_committed"}:
        original = PublicationTerminals.finish

        def finish(self, *args):
            if stage == "reasoning_data_finalized":
                barrier()
            result = original(self, *args)
            if stage == "reasoning_terminal_committed":
                barrier()
            return result

        PublicationTerminals.finish = finish
    elif stage == "reasoning_terminal_before_commit":
        def before_terminal(_connection, _cursor, statement, _params, _context, _many):
            if statement.startswith("INSERT INTO knowledge.publication_terminals"):
                barrier()

        event.listen(host.engine, "before_cursor_execute", before_terminal)
    else:
        raise AssertionError("unknown publication barrier")
